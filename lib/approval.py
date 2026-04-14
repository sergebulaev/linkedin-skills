"""Approval gate helpers.

Every skill that posts to LinkedIn MUST present a draft to the user and wait
for explicit approval before calling Publora. This file is a thin conventions
layer, not runtime enforcement — skills should call `render_approval_card`
to format the draft consistently and then stop until the user says go.
"""
from __future__ import annotations
from typing import Optional


def render_approval_card(
    *,
    kind: str,  # "post" | "comment" | "reply" | "reaction"
    preview_text: str,
    target_url: Optional[str] = None,
    reaction_type: Optional[str] = None,
    char_count: Optional[int] = None,
    extra_context: Optional[dict] = None,
) -> str:
    """Format a standardized approval card for the user to review.

    The card MUST contain:
    - What the action is (post / comment / reply / reaction)
    - The full preview text
    - Target URL if applicable
    - A clear prompt: "reply YES to post or suggest edits"
    """
    lines = [f"## Draft ready for approval — {kind}", ""]
    if target_url:
        lines.append(f"**Target:** {target_url}")
    if reaction_type:
        lines.append(f"**Reaction:** `{reaction_type}`")
    if char_count is None:
        char_count = len(preview_text)
    lines.append(f"**Chars:** {char_count}")
    lines.append("")
    lines.append("**Preview:**")
    lines.append("")
    for pl in preview_text.splitlines() or [""]:
        lines.append(f"> {pl}")
    lines.append("")
    if extra_context:
        lines.append("**Context:**")
        for k, v in extra_context.items():
            lines.append(f"- **{k}**: {v}")
        lines.append("")
    lines.append("Reply **post** / **yes** to publish, or suggest edits.")
    return "\n".join(lines)
