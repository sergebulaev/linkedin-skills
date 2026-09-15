"""The fields the skills actually read must be present in real responses.

Fixtures in `fixtures/` were recorded from live Apify runs on a public post
(texts truncated; shape is the point, not content). They exist because the shape
is the part nothing else checks: `check_actor_inputs.py` proves we ask the actor
the right question, and these prove we can read the answer.

The reply threads in `apify_comments.json` are the specific case that misled a
maintainer: a busy post's newest comments carry `replies: []`, which reads as
"this actor never returns replies" until you sort by relevance.

Offline. No credentials, no network.
"""
from __future__ import annotations

import json
import pathlib
import re
import unittest

FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"


def load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class PostShape(unittest.TestCase):
    """Read by hook-extractor, comment-drafter, reply-handler, engager-analytics."""

    def setUp(self):
        self.post = load("apify_post.json")

    def test_reshare_resolution_fields_are_present(self):
        """`shareUrn` is what lib.repost needs. CLAUDE.md is explicit that an
        activity id must never be hand-converted into a share id, so the field
        has to come from the actor or resharing is guesswork."""
        self.assertTrue(
            any(k in self.post for k in ("shareUrn", "urn", "postId", "activityUrn")),
            f"no id field to resolve a reshare from; got {sorted(self.post)}",
        )

    def test_engagement_counts_are_numbers(self):
        for field in ("numLikes", "numComments"):
            if field in self.post:
                self.assertIsInstance(
                    self.post[field], int, f"{field} is not a number, arithmetic on it will break"
                )

    def test_text_is_reachable(self):
        self.assertTrue(
            any(isinstance(self.post.get(k), str) and self.post[k] for k in ("text", "content", "postText")),
            f"no post text to work from; got {sorted(self.post)}",
        )


class CommentShape(unittest.TestCase):
    """Read by reply-handler (both modes) and thread-monitor."""

    def setUp(self):
        self.comments = load("apify_comments.json")

    def test_fixture_contains_a_reply_thread(self):
        """Without one, every assertion below passes vacuously."""
        self.assertTrue(
            any(c.get("replies") for c in self.comments),
            "re-record the fixture with sort_order='most relevant': no thread in it",
        )

    def test_every_comment_carries_a_replies_list(self):
        """Always present, often empty. reply-handler walks it to find the
        top-level comment for parentComment."""
        for comment in self.comments:
            self.assertIn("replies", comment)
            self.assertIsInstance(comment["replies"], list)

    def test_parent_comment_urn_can_be_built(self):
        """The 2-level flattening rule: a reply's parentComment is the TOP
        comment's id, so both ids have to be readable."""
        from lib.url_parser import build_parent_comment_urn

        threaded = next(c for c in self.comments if c.get("replies"))
        self.assertIn("comment_id", threaded)
        urn = build_parent_comment_urn("urn:li:activity:7320867199693246465", threaded["comment_id"])
        self.assertIn(str(threaded["comment_id"]), urn)
        self.assertTrue(urn.startswith("urn:li:comment:"), urn)
        for reply in threaded["replies"]:
            self.assertIn("comment_id", reply, "a reply with no id cannot be answered")

    def test_author_and_text_are_reachable(self):
        for comment in self.comments:
            author = comment.get("author")
            self.assertTrue(
                isinstance(author, dict) and author.get("name"),
                f"no author name on a comment; got {sorted(comment)}",
            )
            self.assertIsInstance(comment.get("text", ""), str)

    def test_stats_are_numeric_when_present(self):
        for comment in self.comments:
            stats = comment.get("stats") or {}
            for field in ("total_reactions", "comments"):
                if field in stats:
                    self.assertIsInstance(stats[field], int, f"stats.{field} is not a number")


class EngagerShape(unittest.TestCase):
    """Read by engager-analytics, which segments by ICP fit."""

    def setUp(self):
        self.engagers = load("apify_engagers.json")

    def test_type_distinguishes_likers_from_commenters(self):
        """The skill documents `type` as "commenters" | "likers". The client
        stamps it per run, because the actor answers for one audience at a time."""
        types = {e.get("type") for e in self.engagers}
        self.assertTrue(types <= {"likers", "commenters", "reshares"}, f"unexpected types: {types}")
        self.assertNotIn(None, types, "an engager with no type breaks the segmentation")

    def test_subtitle_is_there_to_parse(self):
        """Step 2 of the skill parses `subtitle` into title, company, seniority."""
        self.assertTrue(
            any(e.get("subtitle") for e in self.engagers),
            "no subtitle on any engager, so ICP scoring has nothing to work from",
        )

    def test_profile_url_is_reachable(self):
        for engager in self.engagers:
            self.assertTrue(
                any(engager.get(k) for k in ("url_profile", "profileUrl", "url")),
                f"no profile link on an engager; got {sorted(engager)}",
            )


class ProfileCommentShape(unittest.TestCase):
    """Read by thread-monitor to find the user's own recent comments.

    Note this actor names everything differently from the post-comments one.
    See ShapesDiverge below: thread-monitor reads both in the same run.
    """

    def setUp(self):
        self.comments = load("apify_profile_comments.json")

    def test_each_comment_carries_its_parent_post(self):
        """Step 1 of thread-monitor promises the parent post comes with the
        comment, which is what makes the daily sweep one actor run instead of
        one per comment."""
        for comment in self.comments:
            post = comment.get("post")
            self.assertIsInstance(post, dict, f"no parent post; got {sorted(comment)}")
            self.assertTrue(post.get("post_text") is not None or post.get("post_url"),
                            f"parent post carries neither text nor url; got {sorted(post)}")
            self.assertTrue(comment.get("comment_link"), "no link to the comment itself")

    def test_timestamp_can_be_compared(self):
        """The 6-24h warm window is the whole premise of the skill, so the
        timestamp has to be machine-comparable, not just a formatted string."""
        for comment in self.comments:
            created = comment.get("created_at")
            self.assertIsInstance(created, dict, f"no created_at; got {sorted(comment)}")
            self.assertIsInstance(
                created.get("timestamp"), int,
                f"created_at has no numeric timestamp; got {sorted(created)}",
            )

    def test_comment_urn_is_already_whole(self):
        """Unlike the post-comments actor, this one hands back a full URN, so
        build_parent_comment_urn is neither needed nor correct here.

        Both post kinds turn up in practice: a comment URN wraps either an
        `activity:` or a `ugcPost:` id, so anything parsing it must accept both.
        """
        import re

        pattern = re.compile(r"^urn:li:comment:\((activity|ugcPost):\d+,\d+\)$")
        for comment in self.comments:
            urn = comment.get("comment_urn", "")
            self.assertRegex(urn, pattern, f"unexpected comment urn shape: {urn!r}")


class ShapesDiverge(unittest.TestCase):
    """The two comment readers disagree on every field name.

    thread-monitor calls both in one run: `fetch_user_recent_comments` for the
    user's own comments, then `fetch_post_comments` on each parent post. Code
    written against one shape silently reads `None` from the other, so the
    mapping is pinned here rather than left to be rediscovered.
    """

    MAPPING = {
        # concept:        post-comments   profile-comments
        "text":          ("text",         "comment_text"),
        "author":        ("author",       "commenter"),
        "timestamp":     ("posted_at",    "created_at"),
        "stats":         ("stats",        "comment_stats"),
        "permalink":     ("comment_url",  "comment_link"),
    }

    def setUp(self):
        self.on_post = load("apify_comments.json")[0]
        self.on_profile = load("apify_profile_comments.json")[0]

    def test_each_concept_is_present_under_its_own_name(self):
        for concept, (post_key, profile_key) in self.MAPPING.items():
            self.assertIn(post_key, self.on_post, f"{concept}: {post_key} gone from post comments")
            self.assertIn(profile_key, self.on_profile, f"{concept}: {profile_key} gone from profile comments")

    def test_the_names_really_are_different(self):
        """If an actor ever unifies them, this fails and the warning in
        linkedin-thread-monitor should be removed rather than left to rot."""
        shared = set(self.on_post) & set(self.on_profile)
        self.assertNotIn("text", shared)
        self.assertNotIn("author", shared)


if __name__ == "__main__":
    unittest.main()


class CommentUrnForms(unittest.TestCase):
    """Two URN forms exist and only one is the API's.

    The web permalink and the Apify scraper both use `(activity:X,Y)`.
    LinkedIn's API answers in `(urn:li:activity:X,Y)`, confirmed against a live
    `create_comment` response. `parse_linkedin_url` normalises the short form
    into the long one, and `build_parent_comment_urn` emits the long one, so a
    reply built by following linkedin-reply-handler is correct.

    Pinned because the difference looks like a bug from either direction, and
    "correcting" it would break replies rather than fix them.
    """

    #: Verbatim from a live POST /linkedin-comments response, ids blunted.
    API_FORM = "urn:li:comment:(urn:li:activity:7500000000000000000,7500000000000000001)"

    def test_the_scraper_uses_the_short_form(self):
        for comment in load("apify_profile_comments.json"):
            self.assertRegex(comment["comment_urn"],
                             r"^urn:li:comment:\((?:activity|ugcPost):\d+,\d+\)$")
            self.assertNotIn("(urn:li:", comment["comment_urn"])

    def test_the_parser_normalises_a_pasted_permalink_to_the_api_form(self):
        from lib.url_parser import parse_linkedin_url

        parsed = parse_linkedin_url(
            "https://www.linkedin.com/feed/update/urn:li:activity:7500000000000000000"
            "?commentUrn=urn%3Ali%3Acomment%3A%28activity%3A7500000000000000000"
            "%2C7500000000000000001%29"
        )
        self.assertEqual(parsed["comment_urn"], self.API_FORM)

    def test_the_builder_emits_the_api_form(self):
        from lib.url_parser import build_parent_comment_urn

        self.assertEqual(
            build_parent_comment_urn("urn:li:activity:7500000000000000000", "7500000000000000001"),
            self.API_FORM,
        )

    def test_the_skill_documents_the_form_it_actually_sends(self):
        """The diagram in linkedin-reply-handler showed the short form for a
        while, which is the one that does not work."""
        text = (pathlib.Path(__file__).resolve().parent.parent
                / "skills" / "linkedin-reply-handler" / "SKILL.md").read_text(encoding="utf-8")
        diagram = re.search(r"Top comment by Alice.*?```", text, re.S)
        self.assertIsNotNone(diagram, "the flattening diagram is gone")
        self.assertIn("urn:li:comment:(urn:li:activity:", diagram.group(0))
