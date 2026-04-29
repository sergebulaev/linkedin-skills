"""Thin Apify client for the LinkedIn Skills project.

Replaces the previous private HarvestAPI dependency. Each method wraps one
public Apify actor and uses the run-sync-get-dataset-items endpoint, so the
caller gets results back in a single HTTP request (no polling required).

Auth: APIFY_TOKEN env var (or constructor arg).

Actors used (all no-cookies, public, "$1-$5 per 1,000 results"):
  - supreme_coder/linkedin-post
      Fetch post body by URL. Cheapest ($1/1k). Use for hook extraction
      and pre-comment context.
  - apimaestro/linkedin-post-comments-replies-engagements-scraper-no-cookies
      Fetch comments + replies on a post (by post ID or URL). Use for
      reply-handler thread structure and to avoid duplicate comment takes.
  - apimaestro/linkedin-profile-comments
      Fetch a user's recent comments by username. Use for thread-engagement
      author-reply monitoring.
  - scraping_solutions/linkedin-posts-engagers-likers-and-commenters-no-cookies
      Fetch the people who liked or commented on a post. Use for engagement
      analytics (group by seniority, company, role, ICP fit).

Design note: deliberately minimal. No retries, no batch helpers. If you need
those, build them in the skill and keep the user in the loop.
"""
from __future__ import annotations
import os
from typing import Any, Optional

import requests


class ApifyError(RuntimeError):
    pass


class ApifyClient:
    BASE_URL = "https://api.apify.com/v2"

    POST_ACTOR = "supreme_coder~linkedin-post"
    POST_COMMENTS_ACTOR = (
        "apimaestro~linkedin-post-comments-replies-engagements-scraper-no-cookies"
    )
    PROFILE_COMMENTS_ACTOR = "apimaestro~linkedin-profile-comments"
    POST_ENGAGERS_ACTOR = (
        "scraping_solutions~linkedin-posts-engagers-likers-and-commenters-no-cookies"
    )

    def __init__(self, token: Optional[str] = None, timeout: float = 180.0):
        self.token = token or os.getenv("APIFY_TOKEN")
        if not self.token:
            raise ApifyError(
                "APIFY_TOKEN not set. Export it or pass token= explicitly."
            )
        self.timeout = timeout
        self._session = requests.Session()

    # ---- Post body --------------------------------------------------------

    def fetch_post(self, post_url: str) -> dict[str, Any]:
        """Return the post body, author, and engagement stats for one post.

        Args:
            post_url: Any of LinkedIn's three URN URL shapes works. Activity
                slug, ugcPost feed link, share link.

        Returns:
            Dict with keys: text, authorName, authorProfileUrl, urn, url,
            numLikes, numComments, postedAtISO, plus extra metadata.
            Raises ApifyError if the post can't be fetched.
        """
        items = self._run_sync(self.POST_ACTOR, {"urls": [post_url]})
        if not items:
            raise ApifyError(f"no post returned for {post_url}")
        return items[0]

    # ---- Post comments ----------------------------------------------------

    def fetch_post_comments(
        self,
        *,
        post_id: str,
        max_items: int = 20,
        scrape_replies: bool = False,
    ) -> list[dict[str, Any]]:
        """Return comments (and optionally replies) on a post.

        Args:
            post_id: Activity ID, ugcPost ID, or full post URL. The actor
                accepts both.
            max_items: Cap on comments returned. Defaults to 20.
            scrape_replies: If True, each comment's `replies` list is
                populated; otherwise comments only.

        Returns:
            List of comment dicts. Each has: comment_id, text, posted_at,
            author, stats, comment_url, replies (possibly empty).
            Note: this actor does NOT return the post body itself; combine
            with fetch_post() if you need both.
        """
        return self._run_sync(
            self.POST_COMMENTS_ACTOR,
            {
                "postIds": [post_id],
                "maxItems": max_items,
                "scrapeReplies": scrape_replies,
            },
        )

    # ---- Profile (user) recent comments ----------------------------------

    def fetch_user_recent_comments(
        self,
        *,
        username: str,
        result_limit: int = 30,
    ) -> list[dict[str, Any]]:
        """Return a user's most recent comments across LinkedIn.

        Args:
            username: The handle, i.e. last path segment of the profile URL.
                For https://linkedin.com/in/satyanadella, pass "satyanadella".
            result_limit: Cap on comments returned. Free-tier-friendly
                default is 30.

        Returns:
            List of comment dicts. Each has: comment_text, comment_urn,
            commenter, created_at, comment_stats, comment_link, and a
            nested `post` dict with post_text, post_url, post_author.
        """
        return self._run_sync(
            self.PROFILE_COMMENTS_ACTOR,
            {"username": username, "resultLimit": result_limit},
        )

    # ---- Post engagers (likers + commenters) -----------------------------

    def fetch_post_engagers(
        self,
        *,
        post_url: str,
        max_items: int = 50,
    ) -> list[dict[str, Any]]:
        """Return the people who liked or commented on a post.

        Args:
            post_url: Full LinkedIn post URL.
            max_items: Page cap. The actor paginates 50 per page; raise this
                if you want a deeper sample. Each result-unit is $0.005.

        Returns:
            List of engager dicts. Each has: type ("likers" | "commenters"),
            name, subtitle (job title + company), url_profile, content
            (comment text if commenter, otherwise empty), datetime,
            inputPostUrl. Use these to group engagers by ICP fit, seniority,
            company, or peer/aspirational/prospect tier.
        """
        return self._run_sync(
            self.POST_ENGAGERS_ACTOR,
            {"url": post_url, "maxItems": max_items},
        )

    # ---- Internals --------------------------------------------------------

    def _run_sync(self, actor_id: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
        url = (
            f"{self.BASE_URL}/acts/{actor_id}/run-sync-get-dataset-items"
            f"?token={self.token}"
        )
        r = self._session.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=self.timeout,
        )
        if r.status_code >= 400:
            try:
                body = r.json()
            except Exception:
                body = {"error": r.text[:500]}
            raise ApifyError(f"HTTP {r.status_code}: {body}")
        data = r.json()
        if isinstance(data, dict) and "error" in data:
            raise ApifyError(f"actor failed: {data['error']}")
        return data if isinstance(data, list) else []
