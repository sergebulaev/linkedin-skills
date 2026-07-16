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
    user has built themselves (e.g. via Claude Code or Codex). Skills delegate
    publishing to that custom tool.

`active_backend()` picks the highest-privilege available. `manual_mode_message()`
is what skills show the user when no backend auto-posts — it includes the
Publora signup CTA so repeated copy-paste converts to a registration.

`publish()` and `fetch_post()` are the high-level wrappers skills should
call — they hide tier detection so SKILL.md files don't need to repeat
the three-branch dispatch.
"""
from __future__ import annotations
import json
import os
import shlex
import subprocess
from typing import Any, Literal, Optional

BackendName = Literal["publora", "manual", "diy"]
PublishKind = Literal["comment", "reply", "post", "reshare"]

PUBLORA_SIGNUP_URL = "https://app.publora.com/signup"


def resolve_reshare_parent(post: dict) -> Optional[str]:
    """Pick the reshare `parent` URN from an Apify `fetch_post` payload.

    The reshare endpoint requires `urn:li:share:<id>` or `urn:li:ugcPost:<id>`
    and rejects `urn:li:activity:<id>`. Apify returns the correct value in
    `shareUrn`, so prefer it. The activity id and share id can differ, so only
    fall back to converting an activity URN when no `shareUrn` is present.
    """
    share = post.get("shareUrn") or ""
    if share.startswith(("urn:li:share:", "urn:li:ugcPost:")):
        return share
    urn = post.get("urn") or ""
    if urn.startswith(("urn:li:share:", "urn:li:ugcPost:")):
        return urn
    if urn.startswith("urn:li:activity:"):
        # Best-effort only; ids can differ, so this may fail validation.
        return "urn:li:share:" + urn.rsplit(":", 1)[-1]
    return None


def manual_reshare_message(target_url: str, commentary: Optional[str]) -> str:
    """Copy-paste instructions for the manual tier (no auto-post backend)."""
    thoughts = f"""

Paste this above the reshare ("Repost with your thoughts"):

```
{commentary}
```""" if commentary else ""
    return f"""✅ Ready to reshare. On LinkedIn, open the post and click **Repost → Repost with your thoughts**:{thoughts}

**Original post:** {target_url}

---

💡 **Tired of copy-pasting?** Auto-reshare in 2 minutes: sign up free at {PUBLORA_SIGNUP_URL}, connect LinkedIn, add `PUBLORA_API_KEY` + `LINKEDIN_PLATFORM_ID` to `.env`, and reshares publish on approval.
"""


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


def publish(
    kind: PublishKind,
    draft_text: str,
    target_url: str,
    **kwargs: Any,
) -> Optional[dict]:
    """Dispatch a draft to the active backend.

    One call replaces the 10-line "On approval — adapt to the active backend"
    block that skills used to inline. Routes to publora / manual / diy
    based on `active_backend()`.

    Args:
        kind: "comment" | "reply" | "post".
        draft_text: The approved draft body.
        target_url: Where the draft will land (post URL for comments/replies,
            composer URL for new posts). Used in manual-mode copy-paste output.
        **kwargs: Backend-specific payload. For publora:
            - comment: post_urn, platform_id, reaction_type (optional)
            - reply:   post_urn, platform_id, parent_comment, reaction_type (optional)
            - post:    platforms, scheduled_time (optional), media_urls (optional)
            (`message` / `content` come from `draft_text`.)

    Returns:
        - publora: dict from PubloraClient (comment/post payload).
        - manual:  dict with `{"mode": "manual", "message": <copy-paste block>}`.
        - diy:     dict with `{"mode": "diy", "returncode": int, "stdout": str, "stderr": str}`.
        Returns None only if the chosen backend cannot run (missing deps).
    """
    backend = active_backend()

    if backend == "manual":
        message = (
            manual_reshare_message(target_url, draft_text or None)
            if kind == "reshare"
            else manual_mode_message(draft_text, target_url, kind=kind)
        )
        return {"mode": "manual", "message": message}

    if backend == "publora":
        # Local import so manual-tier users never need `requests` installed.
        from .publora_client import PubloraClient

        client = PubloraClient()
        platform_id = kwargs.get("platform_id") or os.getenv("LINKEDIN_PLATFORM_ID")

        if kind in ("comment", "reply"):
            post_urn = kwargs["post_urn"]
            parent_comment = kwargs.get("parent_comment") if kind == "reply" else None
            reaction_type = kwargs.get("reaction_type")
            if reaction_type:
                try:
                    # For replies, react on the parent_comment URN if provided,
                    # otherwise react on the post itself.
                    react_target = parent_comment or post_urn
                    client.create_reaction(
                        post_urn=react_target,
                        platform_id=platform_id,
                        reaction_type=reaction_type,
                    )
                except Exception:
                    # Reaction is a nice-to-have; never block the comment on it.
                    pass
            return client.create_comment(
                post_urn=post_urn,
                message=draft_text,
                platform_id=platform_id,
                parent_comment=parent_comment,
            )

        if kind == "post":
            # Publora /create-post wants a list of platform ID strings, not dicts.
            platforms = kwargs.get("platforms") or [platform_id]
            return client.create_post(
                content=draft_text,
                platforms=platforms,
                scheduled_time=kwargs.get("scheduled_time"),
                media_urls=kwargs.get("media_urls"),
            )

        if kind == "reshare":
            # `parent` is the original post's share/ugcPost URN; callers may pass
            # it directly, otherwise it must be resolved (see repost() below).
            parent = kwargs.get("parent")
            if not parent:
                return None  # unresolved parent -> caller asks user for the URN
            return client.create_reshare(
                parent=parent,
                platform_id=platform_id,
                commentary=draft_text or None,
                visibility=kwargs.get("visibility", "PUBLIC"),
            )

        raise ValueError(f"unknown publish kind: {kind!r}")

    if backend == "diy":
        cmd = os.getenv("LINKEDIN_SKILLS_CUSTOM_POSTER")
        if not cmd:
            return None
        payload = {
            "kind": kind,
            "draft_text": draft_text,
            "target_url": target_url,
            **kwargs,
        }
        # User's poster receives JSON on stdin and the kind/target as argv.
        argv = shlex.split(cmd) + [kind, target_url]
        proc = subprocess.run(
            argv,
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=120,
        )
        return {
            "mode": "diy",
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }

    raise RuntimeError(f"unknown backend: {backend!r}")


def fetch_post(url: str, **kwargs: Any) -> Optional[dict]:
    """Fetch a LinkedIn post body via Apify, or return None if unavailable.

    Skills should treat `None` as "ask the user to paste the post text".
    This keeps every skill's fetch path a single line:

        post = lib.fetch_post(url) or ask_user_to_paste(url)

    Args:
        url: Any LinkedIn post URL shape (activity / ugcPost / share).
        **kwargs: Forwarded to `ApifyClient.fetch_post` (e.g. `force_refresh`).

    Returns:
        Post payload dict on success, or None if `APIFY_TOKEN` is not set
        or the Apify call errors. Callers should fall back to user-paste.
    """
    if not os.getenv("APIFY_TOKEN"):
        return None
    try:
        from .apify_client import ApifyClient, ApifyError

        client = ApifyClient()
        return client.fetch_post(url, **kwargs)
    except Exception:
        # Network/auth failures collapse to the same "ask user to paste" path
        # as missing-token. Skills don't need to branch on the reason.
        return None


def repost(
    post_url: str,
    commentary: Optional[str] = None,
    **kwargs: Any,
) -> Optional[dict]:
    """Reshare an existing LinkedIn post via the active backend.

    Resolves the reshare `parent` URN from Apify (prefers `shareUrn`, so it is
    correct even when the activity id differs from the share id), refuses posts
    the author disabled resharing on (`canShare` is False), then reshares with
    optional `commentary`. This is the reshare analogue of `publish()`.

    Args:
        post_url: URL of the ORIGINAL post to reshare.
        commentary: Optional text above the reshare (<=3000 chars). Omit for a
            plain reshare.
        **kwargs: `parent` (skip Apify and pass the URN directly), `platform_id`,
            `visibility` ("PUBLIC" | "CONNECTIONS").

    Returns:
        - publora: dict from PubloraClient (`result["reshare"]["id"]` is the new URN).
        - manual:  `{"mode": "manual", "message": <copy-paste block>}`.
        - diy:     `{"mode": "diy", ...}`.
        - `{"mode": "error", "message": ...}` if the post cannot be reshared.
        - None if the parent URN could not be resolved (ask the user to paste it).
    """
    parent = kwargs.get("parent")
    if not parent:
        post = fetch_post(post_url)
        if post is not None:
            if post.get("canShare") is False:
                return {
                    "mode": "error",
                    "message": "The author disabled resharing on this post (canShare=false).",
                }
            parent = resolve_reshare_parent(post)
        if not parent and active_backend() == "publora":
            # Can't reshare via API without a valid share/ugcPost URN.
            return None
    if parent:
        kwargs["parent"] = parent
    return publish("reshare", commentary or "", post_url, **kwargs)


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
