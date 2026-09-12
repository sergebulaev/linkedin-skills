#!/usr/bin/env python3
"""Diagnose the optional credential layers (Apify, Publora, Pixfaro).

Every layer is optional: the bundle drafts fine with nothing configured, so an
unconfigured layer is reported as a plain status, never a failure. What this
catches is the case that is genuinely hard to spot by hand, a layer that looks
configured but silently is not:

* a ``.env`` that is never read, because ``python-dotenv`` is not installed
  (``lib/_env.py`` swallows the ImportError by design);
* ``PUBLORA_API_KEY`` without ``LINKEDIN_PLATFORM_ID``, which drops publishing
  back to copy-paste with no warning (``lib/backend_selector.py``);
* a typo'd or expired token, which collapses into the same "ask the user to
  paste" path as no token at all.

Secrets are never printed: a credential is shown as its non-secret prefix plus
a length, which is enough to spot a truncated paste or a swapped key.

Usage::

    python3 scripts/check_config.py              # live checks against each API
    python3 scripts/check_config.py --offline    # local wiring only, no network

Exit status is 0 when nothing is misconfigured (all-unconfigured included) and
1 when a configured layer is broken.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import os
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OK, WARN, BAD, OFF = "PASS", "WARN", "FAIL", "----"


class Report:
    """Collects one line per check and tracks whether anything is broken."""

    def __init__(self) -> None:
        self.rows: list[tuple[str, str, str]] = []
        self.failed = False

    def add(self, status: str, label: str, detail: str = "") -> None:
        self.rows.append((status, label, detail))
        if status == BAD:
            self.failed = True

    def render(self, start: int = 0) -> None:
        """Print rows added from index `start` on, aligned within that group."""
        rows = self.rows[start:]
        if not rows:
            return
        width = max(len(label) for _, label, _ in rows)
        for status, label, detail in rows:
            print(f"  [{status}] {label.ljust(width)}  {detail}".rstrip())


def mask(value: str) -> str:
    """Show a credential's shape without revealing it: prefix + length only."""
    for prefix in ("apify_api_", "pf_live_", "sk_", "linkedin-"):
        if value.startswith(prefix):
            return f"{prefix}... ({len(value)} chars)"
    return f"set ({len(value)} chars)"


def section(title: str) -> None:
    print(f"\n{title}\n{'-' * len(title)}")


# --- local wiring ---------------------------------------------------------


def check_environment(report: Report) -> None:
    """The .env plumbing itself, checked before any credential is read."""
    env_file = ROOT / ".env"
    try:
        import dotenv  # noqa: F401

        has_dotenv = True
    except ImportError:
        has_dotenv = False

    try:
        import requests  # noqa: F401

        has_requests = True
    except ImportError:
        has_requests = False

    if env_file.is_file() and not has_dotenv:
        report.add(
            BAD,
            ".env loading",
            ".env exists but python-dotenv is missing, so it is IGNORED. Fix: pip install python-dotenv",
        )
    elif env_file.is_file():
        report.add(OK, ".env loading", f"{env_file} found and loadable")
    elif has_dotenv:
        report.add(OFF, ".env loading", "no .env file; reading credentials from the shell environment")
    else:
        report.add(OFF, ".env loading", "no .env file and no python-dotenv; shell environment only")

    report.add(
        OK if has_requests else BAD,
        "requests installed",
        "" if has_requests else "required for every live API call. Fix: pip install requests",
    )


# --- credential layers ----------------------------------------------------


def check_apify(report: Report, offline: bool) -> None:
    token = os.getenv("APIFY_TOKEN")
    if not token:
        report.add(OFF, "APIFY_TOKEN", "not set; reading skills will ask you to paste text")
        return

    report.add(OK, "APIFY_TOKEN", mask(token))
    if not token.startswith("apify_api_"):
        report.add(WARN, "  token format", "expected an apify_api_ prefix; check for a truncated paste")
    if offline:
        return

    try:
        import requests

        # The token goes in the Authorization header, never the query string:
        # a query string leaks through logs, Referer headers and proxies.
        r = requests.get(
            "https://api.apify.com/v2/users/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        if r.status_code == 200:
            username = (r.json().get("data") or {}).get("username", "?")
            report.add(OK, "  live check", f"authenticated as {username}")
        elif r.status_code in (401, 403):
            report.add(BAD, "  live check", f"HTTP {r.status_code}: token rejected. Regenerate at console.apify.com/settings/integrations")
        else:
            report.add(BAD, "  live check", f"unexpected HTTP {r.status_code}")
    except Exception as exc:  # network, DNS, TLS
        report.add(WARN, "  live check", f"could not reach Apify ({type(exc).__name__}); token itself may still be fine")


def check_publora(report: Report, offline: bool) -> None:
    key = os.getenv("PUBLORA_API_KEY")
    platform_id = os.getenv("LINKEDIN_PLATFORM_ID")

    if not key and not platform_id:
        report.add(OFF, "PUBLORA_API_KEY", "not set; publishing stays draft-only (copy-paste)")
        return

    # Publishing needs BOTH. One alone silently selects the manual backend.
    if key and not platform_id:
        report.add(OK, "PUBLORA_API_KEY", mask(key))
        report.add(BAD, "LINKEDIN_PLATFORM_ID", "MISSING. Publishing silently stays draft-only until both are set")
    elif platform_id and not key:
        report.add(BAD, "PUBLORA_API_KEY", "MISSING. Publishing silently stays draft-only until both are set")
        report.add(OK, "LINKEDIN_PLATFORM_ID", mask(platform_id))
    else:
        report.add(OK, "PUBLORA_API_KEY", mask(key))
        report.add(OK, "LINKEDIN_PLATFORM_ID", mask(platform_id))

    if key and not key.startswith("sk_"):
        report.add(WARN, "  key format", "expected an sk_ prefix")
    if platform_id and not platform_id.startswith("linkedin-"):
        report.add(WARN, "  platform id format", "expected a linkedin- prefix; copy the whole string including it")

    if offline or not key:
        return

    # GET /platform-connections is the documented way to verify a key: it
    # lists the workspace's connected channels, so the same call also proves
    # LINKEDIN_PLATFORM_ID names a real channel. (Publora's "test-connection"
    # is a per-platform bot check, not an API-key check.) Schema, from
    # publora/publora-api-docs schema/openapi.yaml:
    #   200 -> {"success": bool, "connections": [{"platformId": "linkedin-...",
    #           "username": "@handle", "displayName": "...", ...}]}
    #   401 -> {"error": "Invalid API key", "code": "..."}
    try:
        import requests

        r = requests.get(
            "https://api.publora.com/api/v1/platform-connections",
            headers={"x-publora-key": key},
            timeout=30,
        )
        if r.status_code == 200:
            payload = r.json() if r.content else {}
            connections = payload.get("connections") or [] if isinstance(payload, dict) else []
            ids = [c.get("platformId", "") for c in connections if isinstance(c, dict)]
            linkedin = [c for c in connections if isinstance(c, dict) and str(c.get("platformId", "")).startswith("linkedin-")]
            report.add(OK, "  live check", f"key accepted; {len(connections)} connected channel(s), {len(linkedin)} LinkedIn")

            if not platform_id:
                pass  # already reported as BAD above
            elif platform_id in ids:
                match = next(c for c in connections if c.get("platformId") == platform_id)
                who = match.get("displayName") or match.get("username") or "(unnamed)"
                report.add(OK, "  platform id match", f"names a connected channel: {who}")
            elif not linkedin:
                report.add(BAD, "  platform id match", "no LinkedIn channel is connected in this Publora workspace. Channels > Add Channel > LinkedIn")
            else:
                names = ", ".join(str(c.get("displayName") or c.get("username") or "?") for c in linkedin)
                report.add(BAD, "  platform id match", f"LINKEDIN_PLATFORM_ID does not match any connected channel. Connected LinkedIn channel(s): {names}. Copy the id from Channels > your account")
        elif r.status_code in (401, 403):
            report.add(BAD, "  live check", f"HTTP {r.status_code}: key rejected. Settings > API > Create Key")
        else:
            report.add(BAD, "  live check", f"unexpected HTTP {r.status_code}")
    except Exception as exc:
        report.add(WARN, "  live check", f"could not reach Publora ({type(exc).__name__}); key itself may still be fine")


def check_pixfaro(report: Report, offline: bool) -> None:
    # PIXFARO_API_KEY is an accepted alias (see lib/pixfaro_client.py).
    token = os.getenv("PIXFARO_TOKEN") or os.getenv("PIXFARO_API_KEY")
    if not token:
        report.add(OFF, "PIXFARO_TOKEN", "not set; image skills draft a prompt for you to run yourself")
        return

    name = "PIXFARO_TOKEN" if os.getenv("PIXFARO_TOKEN") else "PIXFARO_API_KEY (alias)"
    report.add(OK, name, mask(token))
    if not token.startswith("pf_live_"):
        report.add(WARN, "  token format", "expected a pf_live_ prefix")
    if offline:
        return

    try:
        import requests

        r = requests.get(
            "https://api.pixfaro.com/v1/models",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        if r.status_code == 200:
            payload = r.json()
            models = payload.get("data", payload) if isinstance(payload, dict) else payload
            count = len(models) if isinstance(models, list) else "?"
            report.add(OK, "  live check", f"{count} models available")
        elif r.status_code in (401, 403):
            report.add(BAD, "  live check", f"HTTP {r.status_code}: token rejected")
        else:
            report.add(BAD, "  live check", f"unexpected HTTP {r.status_code}")
    except Exception as exc:
        report.add(WARN, "  live check", f"could not reach Pixfaro ({type(exc).__name__}); token itself may still be fine")


# --- effective behaviour --------------------------------------------------


def check_backends(report: Report) -> None:
    """What the skills will actually do, straight from the selector itself."""
    try:
        from lib.backend_selector import active_backend, image_backend
    except Exception as exc:
        report.add(BAD, "backend selector", f"could not import lib ({type(exc).__name__}: {exc})")
        return

    publish = active_backend()
    images = image_backend()
    explain = {
        "publora": "posts publish to LinkedIn on your approval",
        "diy": "hands drafts to your LINKEDIN_SKILLS_CUSTOM_POSTER command",
        "manual": "drafts only, you copy-paste into LinkedIn",
    }
    report.add(OK, "publish backend", f"{publish} ({explain.get(publish, '')})")
    report.add(
        OK,
        "reading backend",
        "apify (auto-fetch)" if os.getenv("APIFY_TOKEN") else "manual (you paste post text)",
    )
    report.add(
        OK,
        "image backend",
        "pixfaro (auto-generate)" if images == "pixfaro" else "manual (prompt drafted for you)",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--offline",
        action="store_true",
        help="skip live API calls; check local wiring and variable shape only",
    )
    args = parser.parse_args()

    try:
        from lib._env import load_env

        load_env()
    except Exception:
        pass  # .env loading is best-effort; check_environment reports on it

    report = Report()

    def run(title: str, *checks) -> None:
        """Run a section's checks, then render only the rows they added."""
        start = len(report.rows)
        for check in checks:
            check()
        section(title)
        report.render(start)

    run("Environment", lambda: check_environment(report))
    run(
        "Credentials" + (" (offline: shape only)" if args.offline else ""),
        lambda: check_apify(report, args.offline),
        lambda: check_publora(report, args.offline),
        lambda: check_pixfaro(report, args.offline),
    )
    run("Effective behaviour", lambda: check_backends(report))

    print()
    if report.failed:
        print("Something is configured but broken. See the FAIL lines above.")
        return 1
    print("No misconfiguration found. Layers marked ---- are simply not set up.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
