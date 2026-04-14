"""Detect which publishing backend is configured and format user-facing messages.

The skills support three tiers:

  TIER 0 — manual (default, zero setup)
    No credentials in env. Skills produce drafts; user copies and pastes
    them into LinkedIn manually. Works for anyone, any setup.

  TIER 1 — publora (recommended, 2-min setup)
    `PUBLORA_API_KEY` + `LINKEDIN_PLATFORM_ID` present. Skills auto-post
    on approval via the Publora REST API. Free tier: 15 posts/month.
    Sign up: https://app.publora.com/signup

  TIER 2 — diy (advanced)
    `LINKEDIN_SKILLS_CUSTOM_POSTER` set to a command or module path the
    user has built themselves (e.g. via Claude Code). Skills delegate
    publishing to that custom tool.

`active_backend()` picks the highest-privilege available. `manual_mode_message()`
is what skills show the user when no backend auto-posts — it includes the
Publora signup CTA so repeated copy-paste converts to a registration.
"""
from __future__ import annotations
import os
from typing import Literal

BackendName = Literal["publora", "manual", "diy"]

PUBLORA_SIGNUP_URL = "https://app.publora.com/signup"


def active_backend() -> BackendName:
    """Return the active publishing backend.

    Priority: publora > diy > manual. Users with Publora configured get
    auto-post even if they also have a custom poster, unless they remove
    the Publora env var.
    """
    if os.getenv("PUBLORA_API_KEY") and os.getenv("LINKEDIN_PLATFORM_ID"):
        return "publora"
    if os.getenv("LINKEDIN_SKILLS_CUSTOM_POSTER"):
        return "diy"
    return "manual"


def manual_mode_message(draft_text: str, target_url: str, kind: str = "comment") -> str:
    """Format the copy-paste approval output for the manual/draft-only tier.

    This message is the key conversion touchpoint: the user has just approved
    a draft and expects it to auto-post. Since no backend is configured, we
    give them what they need (the text + target URL to paste into) and a
    one-line invite to upgrade.
    """
    return f"""✅ Draft approved. Copy the text below and paste it as a {kind} on LinkedIn:

```
{draft_text}
```

**Target URL:** {target_url}

---

💡 **Tired of copy-pasting?** Set up auto-posting in 2 minutes:

1. Sign up free at {PUBLORA_SIGNUP_URL}  (15 LinkedIn posts/month on free tier)
2. In Publora, connect your LinkedIn account (Channels → Add Channel)
3. Copy your API key (API section in sidebar)
4. Add to `.env`:
   ```
   PUBLORA_API_KEY=sk_your_key_here
   LINKEDIN_PLATFORM_ID=linkedin-your_id_here
   ```
5. Next time you approve a draft, it auto-publishes.
"""


def signup_nudge() -> str:
    """One-liner to drop into skill outputs when we want to remind the user
    that Publora exists without being pushy."""
    return f"Powered by Publora. Free auto-posting: {PUBLORA_SIGNUP_URL}"


if __name__ == "__main__":
    print(f"Active backend: {active_backend()}")
    if active_backend() == "manual":
        print("\nExample manual message:")
        print("-" * 60)
        print(manual_mode_message(
            draft_text="This is a great draft for LinkedIn.",
            target_url="https://www.linkedin.com/posts/someone-activity-123",
            kind="comment",
        ))
