#!/usr/bin/env python3
"""Does this bundle work, on this machine, right now?

    python3 scripts/selftest.py              # this checkout: install, accounts, tests, coverage
    python3 scripts/selftest.py --fresh      # clone to a temp dir, build a venv, run there
    python3 scripts/selftest.py --live       # also make one real call per connected layer
    python3 scripts/selftest.py --live --yes # ...without the spending prompt

Five phases, each independently useful:

  install   the things a `git clone` has to get right before anything else can
  accounts  which of Apify / Publora / Pixfaro answer to the keys present, using
            only free endpoints that validate a key without doing any work
  tests     the offline suite in tests/
  coverage  per skill: which layer it needs and whether that layer is live now,
            so the report says which skills are fully working and which quietly
            fall back to copy-paste
  live      one real call per connected layer (opt-in, costs money, reports it)

Exit code is the number of failed phases, so CI and a human read the same run.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
USER_AGENT = "linkedin-skills-selftest/1"

GREEN, RED, YELLOW, GREY, BOLD, OFF = "\033[32m", "\033[31m", "\033[33m", "\033[90m", "\033[1m", "\033[0m"
if not sys.stdout.isatty() or os.getenv("NO_COLOR"):
    GREEN = RED = YELLOW = GREY = BOLD = OFF = ""

PASS, FAIL, WARN, SKIP = f"{GREEN}pass{OFF}", f"{RED}FAIL{OFF}", f"{YELLOW}warn{OFF}", f"{GREY}----{OFF}"


class Phase:
    def __init__(self, title):
        self.title = title
        self.rows = []
        print(f"\n{BOLD}{title}{OFF}")

    def add(self, mark, name, detail=""):
        self.rows.append((mark, name, detail))
        print(f"  [{mark}] {name:<34} {detail}")

    @property
    def failed(self):
        return any(mark == FAIL for mark, _, _ in self.rows)


# --------------------------------------------------------------- install ----
def phase_install(root: pathlib.Path) -> Phase:
    phase = Phase("Install")

    major, minor = sys.version_info[:2]
    ok = (major, minor) >= (3, 10)
    phase.add(PASS if ok else FAIL, "python", f"{major}.{minor} ({'3.10+ needed' if not ok else 'fine'})")

    for module, why in (("requests", "every API layer"), ("dotenv", "reading .env")):
        try:
            __import__(module)
            phase.add(PASS, f"dependency {module}", why)
        except ImportError:
            hard = module == "requests"
            phase.add(FAIL if hard else WARN, f"dependency {module}",
                      f"missing - pip install -r requirements.txt ({why})")

    try:
        result = subprocess.run(
            [sys.executable, "-c",
             "import lib; [getattr(lib, n) for n in "
             "('publish','repost','fetch_post','illustrate','refine','quote_card')]; print('ok')"],
            cwd=root, capture_output=True, text=True, timeout=120,
        )
        phase.add(PASS if result.returncode == 0 else FAIL, "lib imports",
                  "public wrappers resolve" if result.returncode == 0
                  else result.stderr.strip().splitlines()[-1][:80])
    except Exception as exc:
        phase.add(FAIL, "lib imports", f"{type(exc).__name__}: {exc}")

    skills = [d for d in (root / "skills").iterdir() if (d / "SKILL.md").is_file()] \
        if (root / "skills").is_dir() else []
    manifest = root / ".claude-plugin" / "plugin.json"
    promised = None
    if manifest.is_file():
        import re
        match = re.match(r"\s*(\d+)\b", json.loads(manifest.read_text()).get("description", ""))
        promised = int(match.group(1)) if match else None
    phase.add(PASS if promised in (None, len(skills)) else FAIL, "skills present",
              f"{len(skills)} loadable" + (f", manifest promises {promised}" if promised else ""))

    mirror = root / ".claude" / "skills"
    if mirror.is_dir():
        missing = {d.name for d in skills} - {p.name for p in mirror.iterdir()}
        phase.add(PASS if not missing else FAIL, ".claude/skills mirror",
                  "every skill is linked" if not missing else f"not linked: {sorted(missing)}")
    else:
        phase.add(WARN, ".claude/skills mirror", "absent; a plain clone activates nothing")

    sync = root / "scripts" / "sync_codex_marketplace.py"
    if sync.is_file():
        # Compare the tree either side of a regeneration, not against the last
        # commit: uncommitted work in progress is not the same thing as a stale
        # generated package, and conflating them cries wolf on every branch.
        def state():
            out = subprocess.run(["git", "status", "--porcelain", ".codex-marketplace"],
                                 cwd=root, capture_output=True, text=True).stdout
            return {line[3:] for line in out.splitlines()}

        before = state()
        subprocess.run([sys.executable, str(sync)], cwd=root, capture_output=True, timeout=120)
        changed = state() - before
        if not changed:
            phase.add(PASS, "codex package in sync", "regenerating it changes nothing")
        else:
            phase.add(FAIL, "codex package in sync",
                      f"{len(changed)} file(s) were stale: "
                      + ", ".join(sorted(pathlib.Path(f).name for f in changed)[:3])
                      + " - run sync_codex_marketplace.py")
    return phase


# -------------------------------------------------------------- accounts ----
def probe(url, headers, timeout=30):
    import requests

    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT, **headers}, timeout=timeout)
        return r.status_code, r
    except Exception as exc:
        return None, exc


def phase_accounts(offline: bool) -> tuple[Phase, dict]:
    phase = Phase("Accounts")
    live = {"apify": False, "publora": False, "pixfaro": False}

    sys.path.insert(0, str(ROOT))
    from lib._env import load_env

    load_env()

    # --- Apify: reading. Without it every reading skill asks for pasted text.
    token = os.getenv("APIFY_TOKEN")
    if not token:
        phase.add(SKIP, "Apify", "no APIFY_TOKEN; reading skills will ask you to paste")
    elif offline:
        phase.add(PASS, "Apify", f"token present ({len(token)} chars), not verified offline")
    else:
        status, r = probe("https://api.apify.com/v2/users/me", {"Authorization": f"Bearer {token}"})
        if status == 200:
            user = r.json()["data"]
            plan = (user.get("plan") or {}).get("id", "?")
            headroom = ""
            code, limits = probe("https://api.apify.com/v2/users/me/limits",
                                 {"Authorization": f"Bearer {token}"})
            if code == 200:
                data = limits.json().get("data", {})
                used = data.get("current", {}).get("monthlyUsageUsd", 0)
                cap = data.get("limits", {}).get("maxMonthlyUsageUsd")
                headroom = f", ${used:.2f} of ${cap} used" if cap else ""
                if cap and used >= cap * 0.95:
                    phase.add(WARN, "  Apify credit", "under 5% left; runs will start failing")
            phase.add(PASS, "Apify", f"{user.get('username')} on {plan}{headroom}")
            live["apify"] = True
        else:
            phase.add(FAIL, "Apify", f"token rejected (HTTP {status}); reading falls back to paste")

    # --- Publora: writing. Needs both halves to auto-post.
    key, platform = os.getenv("PUBLORA_API_KEY"), os.getenv("LINKEDIN_PLATFORM_ID")
    if not key:
        phase.add(SKIP, "Publora", "no PUBLORA_API_KEY; drafts only, you copy-paste")
    elif offline:
        phase.add(PASS, "Publora", "key present, not verified offline")
    else:
        status, _ = probe("https://api.publora.com/api/v1/platform-limits", {"x-publora-key": key})
        if status == 200:
            if platform:
                phase.add(PASS, "Publora", "key valid, platform id set: posting is automatic")
                live["publora"] = True
            else:
                phase.add(WARN, "Publora",
                          "key valid but LINKEDIN_PLATFORM_ID unset, so posting stays manual")
                # The id is the half people miss, and it is not guessable. Read
                # the account's own connections and hand over the line to paste.
                code, conns = probe("https://api.publora.com/api/v1/platform-connections",
                                    {"x-publora-key": key})
                if code == 200:
                    rows = conns.json()
                    rows = rows.get("connections") or rows.get("data") or rows
                    linked = [c for c in rows if str(c.get("platformId", "")).startswith("linkedin-")] \
                        if isinstance(rows, list) else []
                    if linked:
                        phase.add(SKIP, "  add to .env",
                                  f"LINKEDIN_PLATFORM_ID={linked[0]['platformId']}"
                                  + (f"  ({linked[0].get('name')})" if linked[0].get("name") else ""))
                    else:
                        phase.add(WARN, "  no LinkedIn connection",
                                  "connect one at app.publora.com, then re-run")
        else:
            phase.add(FAIL, "Publora", f"key rejected (HTTP {status})")

    # --- Pixfaro: images. /v1/models is public, so it proves nothing: use /v1/key.
    pix = os.getenv("PIXFARO_TOKEN") or os.getenv("PIXFARO_API_KEY")
    if not pix:
        from lib._env import find_unloaded_token_file

        unloaded = find_unloaded_token_file()
        if unloaded:
            phase.add(FAIL, "Pixfaro", f"defined in {unloaded} but never loaded")
        else:
            phase.add(SKIP, "Pixfaro", "no PIXFARO_TOKEN; image skills draft a prompt instead")
    elif offline:
        phase.add(PASS, "Pixfaro", "token present, not verified offline")
    else:
        status, r = probe("https://api.pixfaro.com/v1/key", {"Authorization": f"Bearer {pix}"})
        if status == 200:
            body = r.json()
            k = body.get("key", {})
            balance = body.get("balance")
            detail = f"key '{k.get('name')}' ({k.get('scope')} scope)"
            phase.add(PASS, "Pixfaro", detail + (f", ${balance} left" if balance is not None else ""))
            live["pixfaro"] = True
            if not body.get("email_verified", True):
                phase.add(WARN, "  Pixfaro email", "unverified; generation stays blocked")
        else:
            phase.add(FAIL, "Pixfaro", f"token rejected (HTTP {status}); keys are shown once")
    return phase, live


# ----------------------------------------------------------------- tests ----
def phase_tests(root: pathlib.Path) -> Phase:
    phase = Phase("Tests")
    if not (root / "tests").is_dir():
        phase.add(WARN, "suite", "no tests/ directory in this checkout")
        return phase
    started = time.time()
    result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
                            cwd=root, capture_output=True, text=True, timeout=900)
    tail = (result.stderr or result.stdout).strip().splitlines()
    count = next((line for line in tail if line.startswith("Ran ")), "ran")
    phase.add(PASS if result.returncode == 0 else FAIL, "offline suite",
              f"{count} in {time.time() - started:.1f}s")
    if result.returncode != 0:
        for line in tail:
            if line.startswith(("FAIL:", "ERROR:")):
                phase.add(FAIL, "  " + line.split(":", 1)[0].lower(), line.split(":", 1)[1].strip()[:70])

    for script, label in (("check_actor_inputs.py", "actor inputs vs schemas"),
                          ("check_frontmatter.py", "skill frontmatter"),
                          ("check_markdown_references.py", "markdown references"),
                          ("check_no_secrets.py", "no tracked credentials")):
        path = root / "scripts" / script
        if not path.is_file():
            continue
        run = subprocess.run([sys.executable, str(path)], cwd=root, capture_output=True, text=True, timeout=300)
        mark = PASS if run.returncode == 0 else (WARN if run.returncode == 2 else FAIL)
        note = "" if run.returncode == 0 else (run.stdout or run.stderr).strip().splitlines()[0][:66]
        phase.add(mark, label, note or "clean")
    return phase


# -------------------------------------------------------------- coverage ----
NEEDS = {
    "linkedin-comment-drafter":   ("apify", "publora"),
    "linkedin-content-planner":   (),
    "linkedin-employee-advocacy": ("publora",),
    "linkedin-engager-analytics": ("apify",),
    "linkedin-hook-extractor":    ("apify",),
    "linkedin-humanizer":         (),
    "linkedin-interviewer":       (),
    "linkedin-post-writer":       ("publora", "pixfaro"),
    "linkedin-profile-optimizer": (),
    "linkedin-reply-handler":     ("apify", "publora"),
    "linkedin-repurposer":        ("publora",),
    "linkedin-thread-monitor":    ("apify",),
}


def phase_coverage(root: pathlib.Path, live: dict) -> Phase:
    phase = Phase("What works right now")
    present = {d.name for d in (root / "skills").iterdir() if (d / "SKILL.md").is_file()}
    unknown = present - set(NEEDS)
    if unknown:
        phase.add(WARN, "unmapped skills", f"{sorted(unknown)} - add them to NEEDS in this script")

    full, degraded, standalone = [], [], []
    for skill in sorted(present & set(NEEDS)):
        needed = NEEDS[skill]
        if not needed:
            standalone.append(skill)
        elif all(live.get(layer) for layer in needed):
            full.append(skill)
        else:
            degraded.append((skill, [l for l in needed if not live.get(l)]))

    phase.add(PASS, "no API needed", f"{len(standalone)}: " + ", ".join(s.split("-", 1)[1] for s in standalone))
    phase.add(PASS if full else SKIP, "fully automatic",
              f"{len(full)}: " + (", ".join(s.split("-", 1)[1] for s in full) if full else "none"))
    for skill, missing in degraded:
        phase.add(WARN, "  " + skill.split("-", 1)[1], f"falls back to manual (no {', '.join(missing)})")
    return phase


# ------------------------------------------------------------------ live ----
def phase_live(live: dict, assume_yes: bool) -> Phase:
    phase = Phase("Live calls (billed)")
    if not any(live.values()):
        phase.add(SKIP, "nothing to call", "no layer is connected")
        return phase
    if not assume_yes:
        print(f"  {YELLOW}This spends real credit: about $0.02 of Apify, nothing on the others.{OFF}")
        if input("  Continue? [y/N] ").strip().lower() not in ("y", "yes"):
            phase.add(SKIP, "declined", "no calls made")
            return phase

    sys.path.insert(0, str(ROOT))
    post = "https://www.linkedin.com/posts/satyanadella_big-day-for-microsoft-365-copilot-im-really-" \
           "activity-7320867199693246465-BAA0/"

    if live["apify"]:
        from lib.apify_client import ApifyClient

        client = ApifyClient()
        try:
            started = time.time()
            comments = client.fetch_post_comments(post_id=post, max_items=3)
            threads = sum(1 for c in comments if c.get("replies"))
            ok = len(comments) <= 3
            phase.add(PASS if ok else FAIL, "Apify read",
                      f"asked 3, got {len(comments)}, {threads} with replies, {time.time() - started:.0f}s")
        except Exception as exc:
            phase.add(FAIL, "Apify read", f"{type(exc).__name__}: {str(exc)[:60]}")

    if live["pixfaro"]:
        from lib.pixfaro_client import PixfaroClient

        try:
            who = PixfaroClient().whoami().get("key", {})
            phase.add(PASS, "Pixfaro identity", f"{who.get('name')} / {who.get('scope')} (free call)")
        except Exception as exc:
            phase.add(FAIL, "Pixfaro identity", f"{type(exc).__name__}: {str(exc)[:60]}")

        # quote_card is the cheapest render and the one whose output must be
        # legible, since the template typesets the text rather than a model
        # drawing it. That makes it the honest smoke test for the image layer.
        try:
            from lib import quote_card

            started = time.time()
            card = quote_card("Every limit you send an actor is ignored unless it is the "
                              "key the actor declares.", size="1:1")
            url = card.get("url")
            phase.add(PASS if url else FAIL, "Pixfaro render",
                      f"quote-card ${card.get('cost', '?')} in {time.time() - started:.0f}s"
                      if url else f"no url in the response: {sorted(card)}")
        except Exception as exc:
            phase.add(FAIL, "Pixfaro render", f"{type(exc).__name__}: {str(exc)[:60]}")

    if live["publora"]:
        # Create a draft, read it back, delete it. A draft has no scheduled time,
        # so nothing is queued and nothing reaches anyone's feed. This is the
        # only way to exercise the write path without publishing.
        from lib.publora_client import PubloraClient, PubloraError

        client, group = PubloraClient(), None
        # Reuse the card rendered above, so the draft also exercises the handover
        # Pixfaro -> media_urls -> Publora, which nothing else covers.
        media_url = locals().get("card", {}).get("url") if live["pixfaro"] else None
        try:
            created = client.create_post(
                content="linkedin-skills selftest draft. Not scheduled, deleted immediately.",
                platforms=[{"platform": "linkedin",
                            "platformId": os.environ["LINKEDIN_PLATFORM_ID"]}],
                media_urls=[media_url] if media_url else None,
            )
            group = created.get("postGroupId")
            phase.add(PASS if group else FAIL, "Publora draft created",
                      f"postGroupId {group}" if group else f"no id back: {sorted(created)}")
        except (PubloraError, KeyError) as exc:
            phase.add(FAIL, "Publora draft created", f"{type(exc).__name__}: {str(exc)[:60]}")

        if group:
            try:
                body = client.get_post(post_group_id=group)
                scheduled = body.get("scheduledTime")
                phase.add(PASS if not scheduled else FAIL, "Publora draft read back",
                          f"status {body.get('status')!r}, nothing scheduled"
                          if not scheduled else f"it has a scheduled time: {scheduled}")
                # The field is `media`, not `mediaFiles`. Reading the wrong name
                # makes a working image pipeline look broken, which is exactly
                # what happened before this line existed.
                media = body.get("media") or []
                if media_url:
                    item = media[0] if media else {}
                    ready = item.get("status") == "ready" and not item.get("failureReason")
                    phase.add(PASS if ready else FAIL, "Publora took the image",
                              f"{item.get('type')} rehosted, status {item.get('status')!r}"
                              if ready else
                              f"attachment missing or unready: {item.get('failureReason') or media}")
            except PubloraError as exc:
                phase.add(FAIL, "Publora draft read back", str(exc)[:60])
            try:
                client.delete_post(post_group_id=group)
                phase.add(PASS, "Publora draft removed", "the account is back as it was")
            except PubloraError as exc:
                phase.add(FAIL, "Publora draft removed",
                          f"CLEAN UP BY HAND: {group} - {str(exc)[:50]}")
    return phase


# ----------------------------------------------------------------- fresh ----
def run_fresh(argv) -> int:
    """Clone this repo into a temp dir, build a venv, and run there - the only
    way to catch what only a clean machine notices."""
    print(f"{BOLD}Fresh install{OFF}")
    temp = pathlib.Path(tempfile.mkdtemp(prefix="linkedin-skills-selftest-"))
    try:
        clone = temp / "clone"
        subprocess.run(["git", "clone", "--quiet", "--depth", "1", f"file://{ROOT}", str(clone)],
                       check=True, capture_output=True, timeout=600)
        print(f"  [{PASS}] {'cloned':<34} {clone}")

        venv = temp / "venv"
        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True, capture_output=True, timeout=600)
        python = venv / "bin" / "python"
        requirements = ["-r", str(clone / "requirements.txt")]
        dev = clone / "requirements-dev.txt"
        if dev.is_file():
            requirements += ["-r", str(dev)]
        install = subprocess.run([str(python), "-m", "pip", "install", "--quiet", *requirements],
                                 capture_output=True, text=True, timeout=900)
        mark = PASS if install.returncode == 0 else FAIL
        print(f"  [{mark}] {'requirements installed':<34} "
              f"{'runtime + maintainer tooling' if install.returncode == 0 else install.stderr.strip()[:60]}")
        if install.returncode != 0:
            return 1

        # The clone carries HEAD, not the working tree. Say so plainly rather
        # than letting python fail on a missing file.
        if not (clone / "scripts" / "selftest.py").is_file():
            print(f"  [{FAIL}] {'selftest in the clone':<34} "
                  f"not committed yet - --fresh checks what a user would clone")
            return 1

        forwarded = [a for a in argv if a != "--fresh"]
        print(f"  [{GREY}····{OFF}] {'handing over to the clone':<34} {' '.join(forwarded) or '(offline)'}\n")
        return subprocess.run([str(python), str(clone / "scripts" / "selftest.py"), *forwarded],
                              cwd=clone).returncode
    finally:
        shutil.rmtree(temp, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fresh", action="store_true", help="clone to a temp dir and run there")
    parser.add_argument("--live", action="store_true", help="make one real call per connected layer")
    parser.add_argument("--yes", action="store_true", help="skip the spending prompt")
    parser.add_argument("--offline", action="store_true", help="never touch the network")
    args = parser.parse_args()

    if args.fresh:
        return run_fresh(sys.argv[1:])

    root = pathlib.Path.cwd() if (pathlib.Path.cwd() / "lib").is_dir() else ROOT
    phases = [phase_install(root)]
    accounts, live = phase_accounts(args.offline)
    phases.append(accounts)
    phases.append(phase_tests(root))
    phases.append(phase_coverage(root, live))
    if args.live and not args.offline:
        phases.append(phase_live(live, args.yes))

    failed = [p.title for p in phases if p.failed]
    print(f"\n{BOLD}{'FAILED: ' + ', '.join(failed) if failed else 'All phases clean'}{OFF}")
    if not any(live.values()) and not args.offline:
        print(f"{GREY}No API layer is connected here. Everything still works, by drafting for "
              f"you to paste. See .env.example.{OFF}")
        if os.getenv("CLAUDECODE"):
            # A connector attached in claude.ai lives in the agent's runtime,
            # not the shell, so this run cannot see it. Saying "nothing is
            # connected" flatly is wrong for anyone using that path.
            print(f"{GREY}This run reads .env and the shell only. A Publora or Pixfaro "
                  f"connector attached in claude.ai is invisible to it and works regardless.{OFF}")
    return len(failed)


if __name__ == "__main__":
    raise SystemExit(main())
