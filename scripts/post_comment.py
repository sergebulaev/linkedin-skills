#!/usr/bin/env python3
"""CLI: draft + post a LinkedIn comment on any post URL.

Usage:
    python scripts/post_comment.py "<POST_URL>" "<COMMENT_TEXT>" [--reaction INTEREST] [--dry-run]

Flow:
    1. Parse URL to URN
    2. Show preview
    3. Prompt "post? yes/no"
    4. On yes: react first, pause 10s, post comment
"""
from __future__ import annotations
import argparse
import os
import sys
import time
from pathlib import Path

# Make repo importable without install
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from lib import PubloraClient, parse_linkedin_url, render_approval_card


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("url")
    ap.add_argument("message")
    ap.add_argument("--reaction", default="INTEREST",
                    help="LIKE | PRAISE | EMPATHY | INTEREST | APPRECIATION | ENTERTAINMENT")
    ap.add_argument("--dry-run", action="store_true", help="Preview only, don't post")
    ap.add_argument("--reply-to", default=None,
                    help="Parent comment ID for threaded replies (optional)")
    args = ap.parse_args()

    parsed = parse_linkedin_url(args.url)
    if not parsed.get("post_urn"):
        print(f"✗ Could not parse URN from URL: {args.url}", file=sys.stderr)
        return 2

    post_urn = parsed["post_urn"]
    platform_id = os.getenv("LINKEDIN_PLATFORM_ID")
    if not platform_id:
        print("✗ LINKEDIN_PLATFORM_ID not set in .env", file=sys.stderr)
        return 2

    parent_comment_urn = None
    if args.reply_to:
        parent_comment_urn = f"urn:li:comment:({post_urn},{args.reply_to})"

    card = render_approval_card(
        kind="reply" if parent_comment_urn else "comment",
        preview_text=args.message,
        target_url=args.url,
        reaction_type=args.reaction,
        extra_context={
            "post_urn": post_urn,
            "parent_comment": parent_comment_urn or "(top-level)",
            "platform": platform_id,
        },
    )
    print(card)
    print()

    if args.dry_run:
        print("(dry-run — nothing posted)")
        return 0

    answer = input("Post? [yes/no]: ").strip().lower()
    if answer not in {"yes", "y", "post"}:
        print("Cancelled.")
        return 0

    client = PubloraClient()
    try:
        client.create_reaction(
            post_urn=post_urn, platform_id=platform_id, reaction_type=args.reaction
        )
        print(f"✓ reacted {args.reaction}")
    except Exception as e:
        print(f"⚠ reaction failed (non-fatal): {e}")

    time.sleep(10)

    try:
        resp = client.create_comment(
            post_urn=post_urn,
            message=args.message,
            platform_id=platform_id,
            parent_comment=parent_comment_urn,
        )
        print(f"✓ posted comment {resp.get('comment', {}).get('id', '?')}")
        return 0
    except Exception as e:
        print(f"✗ comment failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
