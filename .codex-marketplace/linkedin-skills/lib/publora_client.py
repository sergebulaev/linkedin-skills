"""Thin Publora REST client for the LinkedIn Skills project.

Wraps the Publora API endpoints. Verified against the live API 2026-09-15:
- POST   /create-post            (draft when scheduledTime is omitted)
- GET    /get-post/<id>          (status, platforms, media, child posts)
- DELETE /delete-post/<id>       (cancel; see the guard on delete_post)
- GET    /platform-connections   (the channels this key can post to)
- GET    /platform-limits        (character caps, media ceilings; free)
- POST   /linkedin-comments      (top-level or reply via parentComment)
- DELETE /linkedin-comments      (remove a comment we posted)
- POST   /linkedin-reactions     (react to a post or comment)
- POST   /linkedin-reshare       (reshare/repost a post, optional commentary)

The read and cancel endpoints are recent. This docstring claimed for months that
they did not exist, which is why nothing in the bundle used them.

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

    #: Statuses whose content is, or may be, already on the platform. Deleting
    #: one destroys the only record of something that stays live.
    LIVE_STATUSES = ("published", "partially_published")

    def list_platform_connections(self) -> list[dict[str, Any]]:
        """Every channel this key can post to, with its `platformId`.

        The id is the second half of a working Publora setup and the half people
        miss: a key with no platform id behaves exactly like no key at all. It is
        also derivable from the key, which is why `resolve_linkedin_platform_id`
        below asks rather than making the user copy it out of the dashboard.
        """
        r = self._session.get(f"{self.BASE_URL}/platform-connections", timeout=self.timeout)
        payload = self._handle(r)
        rows = payload.get("connections") or payload.get("data") or payload
        return rows if isinstance(rows, list) else []

    def resolve_linkedin_platform_id(self) -> Optional[str]:
        """The account's LinkedIn channel, when there is exactly one.

        Returns None when there are none, or several: with several, guessing
        would publish to the wrong account, which is not a failure worth being
        clever about. The caller then asks, and can list the candidates.
        """
        linkedin = [c.get("platformId") for c in self.list_platform_connections()
                    if str(c.get("platformId", "")).startswith("linkedin-")]
        return linkedin[0] if len(linkedin) == 1 else None

    def get_post(self, *, post_group_id: str) -> dict[str, Any]:
        """Read one post group: status, platforms, scheduled time, children."""
        r = self._session.get(
            f"{self.BASE_URL}/get-post/{post_group_id}", timeout=self.timeout
        )
        return self._handle(r)

    def delete_post(self, *, post_group_id: str, allow_live: bool = False) -> dict[str, Any]:
        """Delete a draft or scheduled post by its `postGroupId`.

        `postGroupId` is what `create_post` returns. This is the only way to
        cancel a post the skills have scheduled: without it an approved-then-
        reconsidered post can only be stopped from the Publora dashboard.

        Note the path shape. Deletion is `DELETE /delete-post/<id>`, with the id
        in the path and no body, unlike `delete_comment`, which is a DELETE to a
        plural collection with a JSON body. A post group that is already gone
        returns HTTP 404 ("Post group not found"), which surfaces here as a
        `PubloraError` rather than a silent success, so callers can tell "I
        deleted it" from "it was not there".

        The status is read first, and a group whose content is already live is
        refused unless `allow_live=True`. Publora's dashboard refuses the same
        thing, but the public endpoint does not: it applies no status guard at
        all, so deleting a published group succeeds and wipes the record, the
        media and the stats of a post that stays up on LinkedIn
        (publora/publora.com#478). The check costs one GET and is the difference
        between cancelling a post and losing one.
        """
        if not allow_live:
            try:
                group = self.get_post(post_group_id=post_group_id)
            except PubloraError:
                group = {}                   # 404 here: let the DELETE report it
            status = (group.get("postGroup") or group).get("status")
            if status in self.LIVE_STATUSES:
                raise PubloraError(
                    f"refusing to delete post group {post_group_id}: status is {status!r}, "
                    "so its content is already on the platform. Deleting it removes the "
                    "record, the media and the stats while the post stays live. Delete the "
                    "post on LinkedIn instead, or pass allow_live=True if you really mean "
                    "to drop the record."
                )
        r = self._session.delete(
            f"{self.BASE_URL}/delete-post/{post_group_id}",
            timeout=self.timeout,
        )
        return self._handle(r)

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
