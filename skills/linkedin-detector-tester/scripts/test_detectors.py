#!/usr/bin/env python3
"""
Tool: test_detectors.py
Purpose: Run input text through 5+ AI detectors in parallel and report divergence.
Usage:
    python test_detectors.py --text "your text here"
    cat draft.txt | python test_detectors.py --stdin
    python test_detectors.py --text "..." --manual    # paste-mode for detectors with no API
Dependencies: requests, python-dotenv (optional)

The point of this tool is NOT to give a definitive AI-or-not score. It is to
document how much the detectors disagree. A 50-point spread between detectors
on the same text is the headline, not any individual score.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import sys
import textwrap
from dataclasses import dataclass
from typing import Callable, Optional

try:
    import requests
except ImportError:
    print("ERROR: install requests first  ->  pip install requests", file=sys.stderr)
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv optional


# ---------------------------------------------------------------------------
# Detector implementations
# Each returns a float 0-100 (% AI probability) or None if unavailable.
# All implementations are stubs / best-effort — APIs change, keys gate access.
# When key is missing, the detector returns None and is dropped from the report.
# ---------------------------------------------------------------------------


@dataclass
class DetectorResult:
    name: str
    score: Optional[float]   # 0-100 % AI, or None
    error: Optional[str] = None


def detect_gptzero(text: str) -> DetectorResult:
    key = os.getenv("GPTZERO_API_KEY")
    if not key:
        return DetectorResult("GPTZero", None, "no API key (set GPTZERO_API_KEY)")
    try:
        r = requests.post(
            "https://api.gptzero.me/v2/predict/text",
            headers={"x-api-key": key, "Content-Type": "application/json"},
            json={"document": text},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        prob = data["documents"][0]["class_probabilities"]["ai"]
        return DetectorResult("GPTZero", round(prob * 100, 1))
    except Exception as e:
        return DetectorResult("GPTZero", None, str(e))


def detect_originality(text: str) -> DetectorResult:
    key = os.getenv("ORIGINALITY_API_KEY")
    if not key:
        return DetectorResult("Originality.ai", None, "no API key (set ORIGINALITY_API_KEY)")
    try:
        r = requests.post(
            "https://api.originality.ai/api/v1/scan/ai",
            headers={"X-OAI-API-KEY": key, "Content-Type": "application/json"},
            json={"content": text, "title": "detector-test"},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        prob = data["score"]["ai"]
        return DetectorResult("Originality.ai", round(prob * 100, 1))
    except Exception as e:
        return DetectorResult("Originality.ai", None, str(e))


def detect_zerogpt(text: str) -> DetectorResult:
    key = os.getenv("ZEROGPT_API_KEY")
    if not key:
        return DetectorResult("ZeroGPT", None, "no API key (set ZEROGPT_API_KEY)")
    try:
        r = requests.post(
            "https://api.zerogpt.com/api/detect/detectText",
            headers={"ApiKey": key, "Content-Type": "application/json"},
            json={"input_text": text},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        score = data["data"]["fakePercentage"]   # 0-100 already
        return DetectorResult("ZeroGPT", round(float(score), 1))
    except Exception as e:
        return DetectorResult("ZeroGPT", None, str(e))


def detect_sapling(text: str) -> DetectorResult:
    key = os.getenv("SAPLING_API_KEY")
    if not key:
        return DetectorResult("Sapling", None, "no API key (set SAPLING_API_KEY)")
    try:
        r = requests.post(
            "https://api.sapling.ai/api/v1/aidetect",
            json={"key": key, "text": text},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        prob = data["score"]
        return DetectorResult("Sapling", round(prob * 100, 1))
    except Exception as e:
        return DetectorResult("Sapling", None, str(e))


def detect_copyleaks(text: str) -> DetectorResult:
    key = os.getenv("COPYLEAKS_API_KEY")
    email = os.getenv("COPYLEAKS_EMAIL")
    if not key or not email:
        return DetectorResult(
            "Copyleaks", None,
            "no creds (set COPYLEAKS_API_KEY and COPYLEAKS_EMAIL)",
        )
    try:
        # Step 1: login -> bearer token
        login = requests.post(
            "https://id.copyleaks.com/v3/account/login/api",
            json={"email": email, "key": key},
            timeout=30,
        )
        login.raise_for_status()
        token = login.json()["access_token"]

        # Step 2: submit text for AI detection
        scan_id = f"detector-test-{abs(hash(text)) % 10**8}"
        r = requests.post(
            f"https://api.copyleaks.com/v2/writer-detector/{scan_id}/check",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={"text": text},
            timeout=60,
        )
        r.raise_for_status()
        data = r.json()
        score = data["summary"]["ai"]   # 0-1
        return DetectorResult("Copyleaks", round(score * 100, 1))
    except Exception as e:
        return DetectorResult("Copyleaks", None, str(e))


# ---------------------------------------------------------------------------
# Manual paste-mode fallback
# Some detectors (Writer.com, Scribbr, Turnitin) have no public API.
# When --manual is set, we prompt the user to open the URL, paste text,
# read the score back, and type it in.
# ---------------------------------------------------------------------------

MANUAL_DETECTORS = {
    "Writer.com":  "https://writer.com/ai-content-detector/",
    "Scribbr":     "https://www.scribbr.com/ai-detector/",
    "QuillBot":    "https://quillbot.com/ai-content-detector",
    "Hive Moderation": "https://hivemoderation.com/ai-generated-content-detection",
}


def detect_manual(name: str, url: str, text: str) -> DetectorResult:
    print(f"\n--- MANUAL: {name} ---")
    print(f"  URL: {url}")
    print(f"  Paste this text (first 80 chars shown): {text[:80]}...")
    raw = input(f"  Score from {name} (0-100, or blank to skip): ").strip()
    if not raw:
        return DetectorResult(name, None, "skipped")
    try:
        return DetectorResult(name, float(raw))
    except ValueError:
        return DetectorResult(name, None, f"invalid input: {raw!r}")


# ---------------------------------------------------------------------------
# Verdict logic
# ---------------------------------------------------------------------------


def verdict_for_spread(spread: float) -> tuple[str, str]:
    """Returns (verdict_label, plain_english_translation)."""
    if spread <= 15:
        return ("CONSENSUS", "detectors agree (still not proof, but consistent)")
    if spread <= 30:
        return ("MIXED", "some signal, but no single score is defensible")
    if spread <= 50:
        return ("DIVERGENT", "the detectors are flipping a coin")
    return ("USELESS", "spread > 50 points; whatever you decide, the opposite detector also 'proves' it")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


API_DETECTORS: list[Callable[[str], DetectorResult]] = [
    detect_gptzero,
    detect_originality,
    detect_zerogpt,
    detect_sapling,
    detect_copyleaks,
]


def run_parallel(text: str) -> list[DetectorResult]:
    results: list[DetectorResult] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(API_DETECTORS)) as pool:
        futures = [pool.submit(fn, text) for fn in API_DETECTORS]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())
    # preserve a stable display order
    order = ["GPTZero", "Originality.ai", "ZeroGPT", "Sapling", "Copyleaks"]
    results.sort(key=lambda r: order.index(r.name) if r.name in order else 99)
    return results


def run_manual(text: str) -> list[DetectorResult]:
    return [detect_manual(name, url, text) for name, url in MANUAL_DETECTORS.items()]


def render_report(text: str, results: list[DetectorResult]) -> dict:
    valid = [r for r in results if r.score is not None]
    scores = [r.score for r in valid]

    print("\n" + "=" * 60)
    preview = text.strip().replace("\n", " ")[:60]
    print(f'Text: "{preview}..."')
    print(f"Length: {len(text.split())} words\n")

    print("Detector scores (% AI probability):")
    for r in results:
        if r.score is not None:
            print(f"  {r.name:<16} {r.score:>5}")
        else:
            print(f"  {r.name:<16}   --   ({r.error})")

    if len(scores) < 2:
        print("\nNot enough detectors returned a score to compute spread.")
        print("Add API keys to .env or use --manual mode.")
        return {"spread": None, "verdict": "INSUFFICIENT_DATA"}

    lo, hi = min(scores), max(scores)
    spread = round(hi - lo, 1)
    label, translation = verdict_for_spread(spread)

    print(f"\nMin: {lo}   Max: {hi}   Spread: {spread}\n")
    print(f"Verdict: {label} — {translation}")
    print("=" * 60)

    return {
        "scores": {r.name: r.score for r in valid},
        "min": lo,
        "max": hi,
        "spread": spread,
        "verdict": label,
        "translation": translation,
    }


def main():
    p = argparse.ArgumentParser(
        description="Run text through multiple AI detectors and report disagreement.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Examples:
              python test_detectors.py --text "Some draft to test"
              cat draft.txt | python test_detectors.py --stdin
              python test_detectors.py --stdin --manual --json out.json
        """),
    )
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--text", help="text to test (inline)")
    src.add_argument("--stdin", action="store_true", help="read text from stdin")

    p.add_argument("--manual", action="store_true",
                   help="run manual paste-mode for detectors without APIs")
    p.add_argument("--json", metavar="PATH",
                   help="also write the full report as JSON to PATH")
    args = p.parse_args()

    text = args.text if args.text else sys.stdin.read()
    text = text.strip()
    if len(text) < 50:
        print("WARNING: text is very short. Detectors are unreliable below 100 words.\n",
              file=sys.stderr)

    results = run_parallel(text)
    if args.manual:
        results.extend(run_manual(text))

    report = render_report(text, results)

    if args.json:
        with open(args.json, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nReport written to {args.json}")


if __name__ == "__main__":
    main()
