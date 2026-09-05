"""Thin Publora REST client for the LinkedIn Skills project.

Wraps the Publora API endpoints. As of 2026-05-11 Publora exposes:
- POST /create-post              (schedule cross-platform post)
- POST /linkedin-comments        (top-level or reply via parentComment)
- DELETE /linkedin-comments      (remove a comment we posted)
- POST /linkedin-reactions       (react to a post or comment)
- POST /linkedin-reshare         (reshare/repost a post, optional commentary)

There is no read-side endpoint at this time (no GET /posts, no list, no
delete-scheduled-post). Post scheduling is fire-and-forget; cancellation
must be done in the Publora dashboard.

Auth header: x-publora-key: sk_...

Design note: this client is deliberately minimal. Skills call exactly one
method per action, after the user has approved a draft rendered via
`lib/approval.py`. All write methods retry on transient 408/429/5xx via the
shared retry decorator.
"""
from __future__ import annotations
import os
import time
import random
from typing import Any, Optional

import requests

from ._env import load_env


class PubloraError(RuntimeError):
    pass


RETRYABLE_STATUSES = {408, 429, 500, 502, 503, 504}


def _retry(attempts: int = 3, base_delay: float = 0.6):
    """Retry decorator for HTTP methods. Triggers on 408/429/5xx and on
    transient network errors. Exponential backoff with jitter."""

    def decorator(fn):
        def wrapper(*args, **kwargs):
            last_exc: Optional[Exception] = None
            for attempt in range(attempts):
                try:
                    return fn(*args, **kwargs)
                except PubloraError as e:
                    msg = str(e)
                    retryable = any(f"HTTP {s}" in msg for s in RETRYABLE_STATUSES)
                    if not retryable or attempt == attempts - 1:
                        raise
                    last_exc = e
                except (requests.ConnectionError, requests.Timeout) as e:
                    if attempt == attempts - 1:
                        raise
                    last_exc = e
                time.sleep(base_delay * (2**attempt) + random.uniform(0, 0.25))
            assert last_exc is not None
            raise last_exc

        return wrapper

    return decorator


class PubloraClient:
    BASE_URL = "https://api.publora.com/api/v1"

    def __init__(self, api_key: Optional[str] = None, timeout: float = 30.0):
        load_env()
        self.api_key = api_key or os.getenv("PUBLORA_API_KEY")

        if not self.api_key:
            raise PubloraError(
                "PUBLORA_API_KEY not set. Export it or pass api_key= explicitly."
            )
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(
            {
                "x-publora-key": self.api_key,
                "Content-Type": "application/json",
            }
        )

    # ---- LinkedIn comments ------------------------------------------------

    def create_comment(
        self,
        *,
        post_urn: str,
        message: str,
        platform_id: str,
        parent_comment: Optional[str] = None,
    ) -> dict[str, Any]:
        """Post a LinkedIn comment (top-level) or a reply (parent_comment set).

        Args:
            post_urn: urn:li:activity:... | urn:li:ugcPost:... | urn:li:share:...
            message: up to 1,250 chars; supports @{urn:li:person:ID|Name} mentions
            platform_id: e.g. "linkedin-fToLopAkEI"
            parent_comment: urn:li:comment:(POST_URN,COMMENT_ID) for replies.
                Note: LinkedIn flattens replies to 2 levels; to reply to a reply,
                use the TOP-level comment URN here, not the reply URN.

        Returns:
            Publora response dict with `comment.id`, `comment.commentUrn`, etc.
        """
        if len(message) > 1250:
            raise PubloraError("message exceeds 1,250 char LinkedIn limit")
        payload = {
            "postedId": post_urn,
            "message": message,
            "platformId": platform_id,
        }
        if parent_comment:
            payload["parentComment"] = parent_comment
        return self._post("/linkedin-comments", payload)

    def delete_comment(
        self,
        *,
        post_urn: str,
        comment_id: str,
        platform_id: str,
    ) -> dict[str, Any]:
        r = self._session.delete(
            self.BASE_URL + "/linkedin-comments",
            json={
                "postedId": post_urn,
                "commentId": comment_id,
                "platformId": platform_id,
            },
            timeout=self.timeout,
        )
        return self._handle(r)

    # ---- LinkedIn reactions -----------------------------------------------

    # Valid reaction types per Publora: LIKE, PRAISE, EMPATHY, INTEREST,
    # APPRECIATION, ENTERTAINMENT. (INSIGHTFUL is NOT valid — map to INTEREST.)
    REACTION_ALIASES = {
        "INSIGHTFUL": "INTEREST",
        "CURIOUS": "INTEREST",
        "FUNNY": "ENTERTAINMENT",
        "LAUGH": "ENTERTAINMENT",
        "LOVE": "APPRECIATION",
        "CELEBRATE": "PRAISE",
    }

    def create_reaction(
        self,
        *,
        post_urn: str,
        platform_id: str,
        reaction_type: str = "LIKE",
    ) -> dict[str, Any]:
        rtype = self.REACTION_ALIASES.get(reaction_type.upper(), reaction_type.upper())
        return self._post(
            "/linkedin-reactions",
            {
                "postedId": post_urn,
                "platformId": platform_id,
                "reactionType": rtype,
            },
        )

    # ---- Posts ------------------------------------------------------------

    def create_post(
        self,
        *,
        content: str,
        platforms: list,
        scheduled_time: Optional[str] = None,
        media_urls: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Create a cross-platform post.

        `platforms` is a list of platform connection ID STRINGS, e.g.
        ["linkedin-xxx"]. The Publora /create-post endpoint requires string IDs;
        passing the old {"platform","platformId"} dict shape returns HTTP 400
        ("Invalid platform ID format"). For backward compatibility, dict entries
        are normalized to their "platformId" here. `scheduled_time` is ISO 8601
        (UTC); if None, the post is created as a draft.
        """
        norm_platforms = [
            p if isinstance(p, str) else (p.get("platformId") or p.get("platform"))
            for p in platforms
        ]
        payload: dict[str, Any] = {
            "content": content,
            "platforms": norm_platforms,
        }
        if scheduled_time:
            payload["scheduledTime"] = scheduled_time
        if media_urls:
            payload["mediaUrls"] = media_urls
        return self._post("/create-post", payload)

    # ---- Reshare (repost) -------------------------------------------------

    def create_reshare(
        self,
        *,
        parent: str,
        platform_id: str,
        commentary: Optional[str] = None,
        visibility: str = "PUBLIC",
    ) -> dict[str, Any]:
        """Reshare (repost) an existing LinkedIn post to the connection's feed.

        `parent` is the URN of the ORIGINAL post and must be
        `urn:li:share:<id>` or `urn:li:ugcPost:<id>` (NOT `urn:li:activity:<id>`,
        which the endpoint rejects). Apify's `fetch_post` returns this directly
        as `shareUrn`; prefer it over converting an activity id, since the two
        numbers can differ.

        `commentary` (<=3000 chars) is the text shown above the reshare ("repost
        with your thoughts"); omit it for a plain reshare. `visibility` is
        `PUBLIC` or `CONNECTIONS`. The endpoint returns HTTP 201; the new reshare
        URN is `result["reshare"]["id"]`.
        """
        payload: dict[str, Any] = {
            "platformId": platform_id,
            "parent": parent,
        }
        if commentary:
            payload["commentary"] = commentary
        if visibility:
            payload["visibility"] = visibility.upper()
        return self._post("/linkedin-reshare", payload)

    # ---- Internals --------------------------------------------------------

    @_retry()
    def _post(self, path: str, json_body: dict[str, Any]) -> dict[str, Any]:
        r = self._session.post(
            self.BASE_URL + path, json=json_body, timeout=self.timeout
        )
        return self._handle(r)

    @staticmethod
    def _handle(r: requests.Response) -> dict[str, Any]:
        if r.status_code >= 400:
            try:
                body = r.json()
            except Exception:
                body = {"error": r.text[:500]}
            raise PubloraError(f"HTTP {r.status_code}: {body}")
        return r.json()
