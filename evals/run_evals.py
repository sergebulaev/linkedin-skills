#!/usr/bin/env python3
"""Do the skills actually do what they claim?

    python3 evals/run_evals.py              # every case
    python3 evals/run_evals.py --case reply-parent
    python3 evals/run_evals.py --list

The tests in `tests/` check the plumbing and the documents. Nothing checks the
thing the bundle actually is: 7,000 lines of instructions an agent follows. This
does, by running the agent against a fixture and grading what comes back.

Each case pastes its input into the prompt rather than relying on a key, which
is both cheaper and the path most users are on: with no APIFY_TOKEN the reading
skills ask you to paste, so this exercises the manual flow end to end.

Graders are deterministic and narrow on purpose. They check claims that have a
right answer — the parentComment for a nested reply, whether a scrubbed draft
kept the user's real numbers — not whether the prose is any good. A grader that
needs taste is a grader that will drift.

Costs one model call per case.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"

GREEN, RED, YELLOW, GREY, BOLD, OFF = "\033[32m", "\033[31m", "\033[33m", "\033[90m", "\033[1m", "\033[0m"
if not sys.stdout.isatty():
    GREEN = RED = YELLOW = GREY = BOLD = OFF = ""


def load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


# --------------------------------------------------------------- fixtures ---
def thread_for_prompt() -> tuple[str, dict]:
    """The recorded comment thread, rendered the way a user would paste it."""
    comments = load("apify_comments.json")
    threaded = next(c for c in comments if c.get("replies"))
    lines = [f"POST: https://www.linkedin.com/feed/update/urn:li:activity:7320867199693246465/", ""]
    lines.append(f"Top-level comment by {threaded['author']['name']} "
                 f"(comment id {threaded['comment_id']}):")
    lines.append(f"  {threaded['text']}")
    for reply in threaded["replies"]:
        lines.append(f"  -> Reply by {reply['author']['name']} (comment id {reply['comment_id']}):")
        lines.append(f"       {reply['text']}")
    return "\n".join(lines), threaded


# ------------------------------------------------------------------ cases ---
def case_reply_parent():
    """LinkedIn flattens threads to two levels. Replying to a reply must target
    the TOP comment's urn. Getting this wrong is a 400 or a misplaced reply, and
    it is the single most specific claim any skill in this bundle makes."""
    thread, threaded = thread_for_prompt()
    deepest = threaded["replies"][-1]
    prompt = (
        "Use the linkedin-reply-handler skill.\n\n"
        f"{thread}\n\n"
        f"I want to reply to the LAST reply, the one by {deepest['author']['name']} "
        f"(comment id {deepest['comment_id']}).\n\n"
        "Draft the reply. Do not publish anything. In your answer, state the exact "
        "parentComment URN you would send to the API on a line of its own."
    )

    def grade(output: str):
        top, wrong = str(threaded["comment_id"]), str(deepest["comment_id"])
        # Only urns carrying real digits count. An answer may also quote a
        # placeholder like `urn:li:comment:(activity:...,...)` while explaining
        # the format, and grading on the last match would read that instead.
        urns = [u for u in re.findall(r"urn:li:comment:\([^)]*\)", output)
                if re.search(r"\d{6,}", u)]
        if not urns:
            return False, "no parentComment urn with real ids stated"
        if not any(top in u for u in urns):
            return False, f"never targets the top-level comment {top}; said {urns[:2]}"
        misdirected = [u for u in urns if wrong in u and top not in u]
        if misdirected:
            return False, f"targets the reply's own id {wrong}: the flattening rule was missed"
        return True, f"correct top-level target {top}"

    return prompt, grade


def case_reply_no_invention():
    """Drafting against a pasted thread, the reply must not attribute claims to
    people who never made them."""
    thread, threaded = thread_for_prompt()
    prompt = ("Use the linkedin-reply-handler skill.\n\n" + thread +
              "\n\nDraft a reply to the top-level comment. Do not publish. Show the draft only.")

    def grade(output: str):
        invented = [n for n in ("Satya Nadella", "Microsoft CEO") if n in output]
        draft = output.lower()
        if "http" in draft and "linkedin.com" not in draft:
            return False, "the draft carries an outside link nobody asked for"
        if invented:
            return False, f"puts words on people not in the thread: {invented}"
        return True, "no invented participants, no stray links"

    return prompt, grade


def case_hook_formula():
    """hook-extractor claims it returns which of the 20 canonical formulas a
    post used. The answer must be one that exists."""
    defined = set(re.findall(r"^## (F\d+) ",
                             (ROOT / "references" / "hook-formulas.md").read_text(), re.M))
    post = ("I deleted our $40k/yr analytics stack on a Tuesday.\n\n"
            "Three weeks later nobody on the team had noticed.\n\n"
            "Here is what we replaced it with, and the one thing that actually broke.")
    prompt = ("Use the linkedin-hook-extractor skill on this post. Do not fetch anything, "
              "the text is here.\n\n" + post +
              "\n\nName the formula by its F-number and quote the hook line you matched.")

    def grade(output: str):
        cited = set(re.findall(r"\b(F\d{1,2})\b", output))
        if not cited:
            return False, "named no formula at all"
        unknown = cited - defined
        if unknown:
            return False, f"cited formulas that do not exist: {sorted(unknown)}"
        if "deleted our $40k" not in output and "$40k" not in output:
            return False, "did not quote the hook line from the post"
        return True, f"cited {sorted(cited)} and quoted the hook"

    return prompt, grade


def case_humanizer_keeps_facts():
    """The scrub must remove AI vocabulary and keep the user's real numbers. A
    humanizer that launders away a figure is worse than none."""
    draft = ("In today's rapidly evolving landscape, we leveraged a robust framework to "
             "unlock synergies. We cut deploy time from 47 minutes to 6, and support "
             "tickets fell 31% in Q3. It's not just about speed, it's about delving deeper "
             "into what truly matters for our stakeholders.")
    prompt = ("Use the linkedin-humanizer skill on this draft. Return the rewritten draft "
              "only, no commentary.\n\n" + draft)

    def grade(output: str):
        missing = [n for n in ("47", "6", "31", "Q3") if n not in output]
        if missing:
            return False, f"dropped the user's own figures: {missing}"
        markers = [w for w in ("leverage", "robust", "synergie", "delve", "rapidly evolving",
                               "it's not just about", "truly matters") if w in output.lower()]
        if markers:
            return False, f"left AI markers in place: {markers}"
        return True, "figures kept, markers gone"

    return prompt, grade


def case_engagers_no_fabrication():
    """Segmenting must work from the people supplied, and only those.

    Graded on two things with a right answer: every supplied engager appears,
    and any roster size the answer states matches what it was given. Inventing a
    person shows up as an inflated count; dropping one shows up directly.

    Not graded: whether the ICP scoring is any good, or whether an attribute was
    embellished. Those need judgement, and a grader that needs judgement drifts.
    """
    engagers = load("apify_engagers.json")
    listed = "\n".join(
        f"- {e.get('name')} | {e.get('subtitle')} | {e.get('type')}" for e in engagers)
    prompt = ("Use the linkedin-engager-analytics skill. Here are the engagers, already "
              "fetched, so do not fetch anything and do not invent any.\n\n" + listed +
              "\n\nMy ICP is B2B SaaS founders. Segment these and give the outbound actions.")

    def grade(output: str):
        real = [str(e["name"]) for e in engagers if e.get("name")]
        dropped = [n for n in real if n not in output]
        if dropped:
            return False, f"silently dropped supplied engagers: {dropped}"
        # Any roster size the answer commits to has to be the size it was handed.
        claimed = {int(n) for n in re.findall(
            r"\b(\d{1,3})\s+(?:engagers?|people|profiles?|total)\b", output, re.I)}
        inflated = sorted(n for n in claimed if n > len(real))
        if inflated:
            return False, f"claims {inflated} engagers, was given {len(real)}"
        return True, f"all {len(real)} supplied used, no inflated roster"

    return prompt, grade


CASES = {
    "reply-parent": ("linkedin-reply-handler: the 2-level flattening rule", case_reply_parent),
    "reply-no-invention": ("linkedin-reply-handler: invents no participants", case_reply_no_invention),
    "hook-formula": ("linkedin-hook-extractor: names a formula that exists", case_hook_formula),
    "humanizer-facts": ("linkedin-humanizer: scrubs markers, keeps figures", case_humanizer_keeps_facts),
    "engagers-real": ("linkedin-engager-analytics: fabricates nobody", case_engagers_no_fabrication),
}


# ----------------------------------------------------------------- runner ---
def ask(prompt: str, timeout: int) -> tuple[str, str]:
    """Run the agent headless from the repo root, so .claude/skills is found."""
    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--output-format", "text"],
            cwd=ROOT, capture_output=True, text=True, timeout=timeout,
        )
    except FileNotFoundError:
        return "", "the `claude` CLI is not on PATH"
    except subprocess.TimeoutExpired:
        return "", f"no answer within {timeout}s"
    if result.returncode != 0:
        return "", (result.stderr or result.stdout).strip().splitlines()[-1][:90]
    return result.stdout, ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--case", action="append", help="run only these (repeatable)")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--timeout", type=int, default=420)
    parser.add_argument("--save", type=pathlib.Path, help="write every answer here for reading")
    args = parser.parse_args()

    if args.list:
        for key, (title, _) in CASES.items():
            print(f"  {key:22} {title}")
        return 0

    selected = args.case or list(CASES)
    unknown = [c for c in selected if c not in CASES]
    if unknown:
        print(f"no such case: {unknown}. --list to see them all")
        return 2

    print(f"{BOLD}Skill behaviour{OFF}  ({len(selected)} cases, one model call each)\n")
    transcripts, failures = {}, 0
    for key in selected:
        title, build = CASES[key]
        prompt, grade = build()
        started = time.time()
        output, error = ask(prompt, args.timeout)
        transcripts[key] = {"prompt": prompt, "output": output, "error": error}
        if error:
            print(f"  [{YELLOW}skip{OFF}] {title:<52} {error}")
            continue
        passed, detail = grade(output)
        mark = f"{GREEN}pass{OFF}" if passed else f"{RED}FAIL{OFF}"
        failures += 0 if passed else 1
        print(f"  [{mark}] {title:<52} {detail} ({time.time() - started:.0f}s)")

    if args.save:
        args.save.write_text(json.dumps(transcripts, indent=1, ensure_ascii=False))
        print(f"\n{GREY}answers written to {args.save}{OFF}")
    print(f"\n{BOLD}{'All cases passed' if not failures else f'{failures} case(s) failed'}{OFF}")
    return failures


if __name__ == "__main__":
    raise SystemExit(main())
