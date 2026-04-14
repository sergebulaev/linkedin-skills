"""LinkedIn URL → URN parser.

Handles three common shapes:

1. Post URL (from "Copy link to post"):
   https://www.linkedin.com/posts/SLUG-activity-ACTIVITY_ID-XX

2. Comment URL (from "Copy link to comment"):
   https://www.linkedin.com/feed/update/urn:li:activity:ACTIVITY_ID?commentUrn=urn%3Ali%3Acomment%3A%28activity%3AACTIVITY_ID%2CCOMMENT_ID%29

3. Share/ugcPost URL:
   https://www.linkedin.com/posts/SLUG-share-SHARE_ID-XX
   or /feed/update/urn:li:ugcPost:XYZ

Returns normalized dict:
    {
      "post_activity_id": "<numeric>" | None,
      "post_urn": "urn:li:activity:<id>" | "urn:li:ugcPost:<id>" | "urn:li:share:<id>",
      "comment_id": "<numeric>" | None,
      "comment_urn": "urn:li:comment:(<post_urn>,<comment_id>)" | None,
      "url_type": "post" | "comment" | "unknown",
    }

Note: the activity ID in the URL slug is NOT always the same as the canonical URN used by LinkedIn's backend (ugcPost vs activity vs share). For posting comments, use the post_urn returned here by default but fall back to resolving via HarvestAPI /linkedin/post-comments (inspect the `postId` field of any existing comment) when the direct URN 404s.
"""
from __future__ import annotations
import re
from urllib.parse import urlparse, unquote
from typing import Optional, TypedDict


class ParsedLinkedInUrl(TypedDict, total=False):
    post_activity_id: Optional[str]
    post_urn: Optional[str]
    comment_id: Optional[str]
    comment_urn: Optional[str]
    url_type: str


ACTIVITY_SLUG_RE = re.compile(r"activity[-:](\d{18,25})")
SHARE_SLUG_RE = re.compile(r"share[-:](\d{18,25})")
UGCPOST_SLUG_RE = re.compile(r"ugcPost[-:](\d{18,25})")
COMMENT_URN_RE = re.compile(
    r"urn:li:comment:\("
    r"(?:urn:li:)?(activity|ugcPost|share):(\d+)"
    r"\s*,\s*(\d+)"
    r"\)"
)


def parse_linkedin_url(url: str) -> ParsedLinkedInUrl:
    """Parse any LinkedIn post or comment URL into structured URNs.

    >>> p = parse_linkedin_url("https://www.linkedin.com/posts/dharmesh_activity-7448808898326654978-iW20")
    >>> p["post_activity_id"]
    '7448808898326654978'
    >>> p["post_urn"]
    'urn:li:activity:7448808898326654978'
    >>> p["url_type"]
    'post'
    """
    decoded = unquote(url)
    out: ParsedLinkedInUrl = {
        "post_activity_id": None,
        "post_urn": None,
        "comment_id": None,
        "comment_urn": None,
        "url_type": "unknown",
    }

    # Try comment URN first (commentUrn=... query param or path)
    m = COMMENT_URN_RE.search(decoded)
    if m:
        kind, post_id, comment_id = m.groups()
        out["comment_id"] = comment_id
        if kind == "activity":
            out["post_urn"] = f"urn:li:activity:{post_id}"
            out["post_activity_id"] = post_id
        elif kind == "ugcPost":
            out["post_urn"] = f"urn:li:ugcPost:{post_id}"
        elif kind == "share":
            out["post_urn"] = f"urn:li:share:{post_id}"
        out["comment_urn"] = f"urn:li:comment:({out['post_urn']},{comment_id})"
        out["url_type"] = "comment"
        return out

    # Post URL variants
    for pattern, kind in [
        (UGCPOST_SLUG_RE, "ugcPost"),
        (SHARE_SLUG_RE, "share"),
        (ACTIVITY_SLUG_RE, "activity"),
    ]:
        m = pattern.search(decoded)
        if m:
            pid = m.group(1)
            out["post_urn"] = f"urn:li:{kind}:{pid}"
            if kind == "activity":
                out["post_activity_id"] = pid
            out["url_type"] = "post"
            return out

    return out


def build_parent_comment_urn(post_urn: str, parent_comment_id: str) -> str:
    """Format a parentComment URN given a post URN and the top-level comment id.

    LinkedIn flattens reply threads to 2 levels: if you're replying to a reply,
    parentComment should still point to the top-level comment, not the reply.
    """
    return f"urn:li:comment:({post_urn},{parent_comment_id})"


if __name__ == "__main__":
    import json
    import sys

    examples = sys.argv[1:] or [
        "https://www.linkedin.com/posts/dharmesh_activity-7448808898326654978-iW20",
        "https://www.linkedin.com/feed/update/urn:li:activity:7448387840113184768?commentUrn=urn%3Ali%3Acomment%3A%28activity%3A7448387840113184768%2C7449095071892672512%29",
        "https://www.linkedin.com/posts/ivantsybaev_one-broker-share-7449499107418669056-ZYt7",
    ]
    for u in examples:
        print(u)
        print(json.dumps(parse_linkedin_url(u), indent=2))
        print()
