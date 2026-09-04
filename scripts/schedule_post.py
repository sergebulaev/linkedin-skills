#!/usr/bin/env python3
"""CLI: schedule an approved LinkedIn post via Publora at 10:00 local time.

Usage:
    python scripts/schedule_post.py --file draft.txt --angle <slug> [--source URL ...] [--dry-run]
    python scripts/schedule_post.py --selftest

Schedule rule: today at 10:00 local. If it is already past 10:00, now + 5 min
(Publora treats a missing scheduledTime as "save as draft", so there is no
true "post immediately" call, so the nearest thing is a schedule a few minutes out).

Every successful schedule appends one JSON line to testing/linkedin-routine-log.jsonl
so the next run can rotate to a different angle. testing/ is gitignored.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

LOG_PATH = ROOT / "testing" / "linkedin-routine-log.jsonl"
POST_HOUR = 10
LEAD_MINUTES = 5


def slot(now: datetime) -> datetime:
    """Today's 10:00 slot in `now`'s timezone, or now+5min if that has passed."""
    ten = now.replace(hour=POST_HOUR, minute=0, second=0, microsecond=0)
    return ten if now < ten else now + timedelta(minutes=LEAD_MINUTES)


def selftest() -> int:
    tz = timezone(timedelta(hours=-6))
    early = datetime(2026, 9, 7, 8, 30, tzinfo=tz)
    assert slot(early) == datetime(2026, 9, 7, 10, 0, tzinfo=tz)
    late = datetime(2026, 9, 7, 14, 20, tzinfo=tz)
    assert slot(late) == datetime(2026, 9, 7, 14, 25, tzinfo=tz)
    # 10:00 exactly counts as passed -> nudged forward, never scheduled in the past
    assert slot(datetime(2026, 9, 7, 10, 0, tzinfo=tz)) > datetime(2026, 9, 7, 10, 0, tzinfo=tz)
    assert slot(early).astimezone(timezone.utc).isoformat() == "2026-09-07T16:00:00+00:00"
    print("selftest OK")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--file", help="path to the final post text (UTF-8)")
    ap.add_argument("--angle", default="", help="sub-topic slug used, for rotation logging")
    ap.add_argument("--source", action="append", default=[], help="source URL/title (repeatable)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()
    if not args.file:
        ap.error("--file is required")

    text = Path(args.file).read_text(encoding="utf-8").strip()
    if not text:
        print("✗ draft file is empty", file=sys.stderr)
        return 2
    if len(text) > 3000:
        print(f"✗ draft is {len(text)} chars, LinkedIn caps posts at 3000", file=sys.stderr)
        return 2

    when = slot(datetime.now().astimezone())
    scheduled_utc = when.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"→ {len(text)} chars, scheduled {when.isoformat()} (UTC {scheduled_utc})")

    if args.dry_run:
        print("(dry-run, nothing scheduled)")
        return 0

    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")

    from lib import active_backend, publish

    backend = active_backend()
    if backend != "publora":
        print(f"✗ backend is {backend!r}, expected 'publora'. Check PUBLORA_API_KEY "
              f"and LINKEDIN_PLATFORM_ID in .env", file=sys.stderr)
        return 2

    try:
        resp = publish(
            "post",
            text,
            "https://www.linkedin.com/feed/",
            scheduled_time=scheduled_utc,
        )
    except Exception as e:
        print(f"✗ publora schedule failed: {e}", file=sys.stderr)
        return 1

    r = resp or {}
    post_id = r.get("postGroupId") or r.get("postId") or r.get("id") or json.dumps(r)[:200]
    entry = {
        "date": when.date().isoformat(),
        "angle": args.angle,
        "sources": args.source,
        "scheduled_utc": scheduled_utc,
        "post_id": post_id,
        "chars": len(text),
    }
    LOG_PATH.parent.mkdir(exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"✓ scheduled. publora post id: {post_id}")
    print(f"  raw response: {json.dumps(resp, ensure_ascii=False)[:400]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
