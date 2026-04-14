"""Thin Publora REST client for the LinkedIn Skills project.

Wraps the Publora API endpoints most relevant to LinkedIn engagement:
- POST /linkedin-comments (with optional parentComment for replies)
- POST /linkedin-reactions
- POST /posts (schedule posts)
- DELETE /linkedin-comments

API reference:
  /home/sbulaev/p/publora.com/publora-api-docs/docs/endpoints/linkedin-comments.md
  /home/sbulaev/p/publora.com/publora-api-docs/docs/endpoints/linkedin-reactions.md
  /home/sbulaev/p/publora.com/publora-api-docs/docs/endpoints/create-post.md

Auth header: x-publora-key: sk_...

Design note: this client is deliberately minimal. Skills call exactly one
method per action, after the user has approved a draft rendered via
`lib/approval.py`. No automatic retries, no batch operations — if you need
those, build them in the skill and keep the user in the loop.
"""
from __future__ import annotations
import os
from typing import Any, Optional

import requests


class PubloraError(RuntimeError):
    pass


class PubloraClient:
    BASE_URL = "https://api.publora.com/api/v1"

    def __init__(self, api_key: Optional[str] = None, timeout: float = 30.0):
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
        platforms: list[dict[str, str]],
        scheduled_time: Optional[str] = None,
        media_urls: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Create a cross-platform post.

        `platforms` is a list of {"platform": "linkedin", "platformId": "linkedin-xxx"}
        dicts. `scheduled_time` is ISO 8601 (UTC); if None, Publora schedules ~90s
        in the future by default.
        """
        payload: dict[str, Any] = {
            "content": content,
            "platforms": platforms,
        }
        if scheduled_time:
            payload["scheduledTime"] = scheduled_time
        if media_urls:
            payload["mediaUrls"] = media_urls
        return self._post("/posts", payload)

    # ---- Internals --------------------------------------------------------

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
