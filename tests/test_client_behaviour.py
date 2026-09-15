"""What the clients do before anything leaves the machine.

`check_actor_inputs.py` proves the payload keys exist in the actor's schema.
These prove the values: clamps applied, budgets split, bad arguments refused,
and the cache keyed on everything that changes the answer.

Offline. The network layer is replaced, so nothing is spent and no key is read.
"""
from __future__ import annotations

import unittest
from unittest import mock

from lib.apify_client import ApifyClient


def client_with_spy(rows_per_call=0):
    """An ApifyClient whose actor runs are recorded instead of made."""
    calls = []

    def spy(self, actor_id, payload, *, force_refresh=False):
        calls.append({"actor": actor_id, **payload})
        return [{"name": f"row{i}"} for i in range(rows_per_call)]

    client = ApifyClient.__new__(ApifyClient)        # no token, never constructed
    return client, calls, mock.patch.object(ApifyClient, "_run_sync", spy)


class CommentLimits(unittest.TestCase):
    def test_limit_is_clamped_to_the_actors_maximum(self):
        """The schema caps `limit` at 100. Asking for more used to be sent
        verbatim, which the actor ignored entirely."""
        client, calls, patch = client_with_spy()
        with patch:
            client.fetch_post_comments(post_id="1", max_items=5000)
        self.assertEqual(calls[0]["limit"], 100)

    def test_a_small_limit_is_passed_through(self):
        client, calls, patch = client_with_spy()
        with patch:
            client.fetch_post_comments(post_id="1", max_items=7)
        self.assertEqual(calls[0]["limit"], 7)

    def test_sort_defaults_to_relevance_not_the_actors_default(self):
        """The actor defaults to "most recent", whose newest comments carry no
        reply threads at all on a busy post. Every caller here needs threads."""
        client, calls, patch = client_with_spy()
        with patch:
            client.fetch_post_comments(post_id="1")
        self.assertEqual(calls[0]["sortOrder"], "most relevant")

    def test_an_unknown_sort_is_refused_before_it_is_billed(self):
        client, _, patch = client_with_spy()
        with patch, self.assertRaises(ValueError):
            client.fetch_post_comments(post_id="1", sort_order="newest")

    def test_the_dead_argument_is_accepted_and_not_forwarded(self):
        """`scrape_replies` is not an input of that actor and never was. It stays
        in the signature so existing callers keep working."""
        client, calls, patch = client_with_spy()
        with patch:
            client.fetch_post_comments(post_id="1", scrape_replies=True)
        self.assertNotIn("scrapeReplies", calls[0])

    def test_the_run_summary_row_is_dropped(self):
        """The actor appends {"summary": {...}} to the dataset, and returns it
        alone when a post has no comments. Callers must never see it."""
        def spy(self, actor_id, payload, *, force_refresh=False):
            return [{"summary": {"total": 0}}, {"text": "a real comment"}]

        client = ApifyClient.__new__(ApifyClient)
        with mock.patch.object(ApifyClient, "_run_sync", spy):
            rows = client.fetch_post_comments(post_id="1")
        self.assertEqual(rows, [{"text": "a real comment"}])


class EngagerBudget(unittest.TestCase):
    def test_both_audiences_are_asked_for_by_default(self):
        """`type` is required and defaults to likers, so omitting it returned
        likers only while the skill promised commenters too."""
        client, calls, patch = client_with_spy()
        with patch:
            client.fetch_post_engagers(post_url="u")
        self.assertEqual([c["type"] for c in calls], ["likers", "commenters"])

    def test_the_budget_is_split_not_multiplied(self):
        """max_items is the total across audiences, so asking for both costs the
        same as asking for one. The skill's cost table depends on this."""
        client, calls, patch = client_with_spy(rows_per_call=50)
        with patch:
            rows = client.fetch_post_engagers(post_url="u", max_items=100)
        self.assertEqual([c["resultsLimit"] for c in calls], [50, 50])
        self.assertEqual(len(rows), 100)

    def test_the_total_is_never_exceeded(self):
        client, _, patch = client_with_spy(rows_per_call=40)
        with patch:
            rows = client.fetch_post_engagers(post_url="u", max_items=9)
        self.assertLessEqual(len(rows), 9)

    def test_each_row_is_stamped_with_its_audience(self):
        client, _, patch = client_with_spy(rows_per_call=2)
        with patch:
            rows = client.fetch_post_engagers(post_url="u", max_items=4)
        self.assertEqual({r["type"] for r in rows}, {"likers", "commenters"})

    def test_cached_rows_are_not_mutated(self):
        """Rows come out of an LRU cache. Stamping `type` onto them in place
        would poison the cache for the other audience."""
        shared = [{"name": "x"}]

        def spy(self, actor_id, payload, *, force_refresh=False):
            return shared

        client = ApifyClient.__new__(ApifyClient)
        with mock.patch.object(ApifyClient, "_run_sync", spy):
            client.fetch_post_engagers(post_url="u", max_items=4)
        self.assertEqual(shared, [{"name": "x"}], "the cached row was written to")

    def test_an_unknown_audience_is_refused(self):
        client, _, patch = client_with_spy()
        for bad in ((), ("likes",), ("likers", "typo")):
            with self.subTest(types=bad), patch, self.assertRaises(ValueError):
                client.fetch_post_engagers(post_url="u", types=bad)


class ProfileCommentLimits(unittest.TestCase):
    def test_limit_is_clamped_to_the_schema_maximum(self):
        client, calls, patch = client_with_spy()
        with patch:
            client.fetch_user_recent_comments(username="someone", result_limit=99999)
        self.assertEqual(calls[0]["limit"], 3000)

    def test_the_username_is_sent_as_a_list(self):
        """The actor takes `usernames`, plural. The singular form was ignored."""
        client, calls, patch = client_with_spy()
        with patch:
            client.fetch_user_recent_comments(username="someone")
        self.assertEqual(calls[0]["usernames"], ["someone"])


class BackendDispatch(unittest.TestCase):
    """Which layer answers, given what is configured. No key means manual, and
    manual must still produce something the user can act on."""

    def test_no_credentials_means_manual_everywhere(self):
        from lib import backend_selector

        with mock.patch.dict("os.environ", {}, clear=True):
            self.assertEqual(backend_selector.active_backend(), "manual")
            self.assertEqual(backend_selector.image_backend(), "manual")

    def test_a_custom_poster_takes_over_from_manual(self):
        from lib import backend_selector

        with mock.patch.dict("os.environ", {"LINKEDIN_SKILLS_CUSTOM_POSTER": "/bin/true"}, clear=True):
            self.assertEqual(backend_selector.active_backend(), "diy")

    def test_publora_needs_both_halves(self):
        """A key with no platform id looks exactly like no Publora at all, which
        is why the manual message names the half that is missing."""
        from lib import backend_selector

        with mock.patch.dict("os.environ", {"PUBLORA_API_KEY": "k"}, clear=True):
            self.assertNotEqual(backend_selector.active_backend(), "publora")

    def test_the_manual_message_tells_the_user_what_to_do(self):
        from lib import backend_selector

        with mock.patch.dict("os.environ", {}, clear=True):
            message = backend_selector.manual_mode_message(
                "post", "a drafted post", "https://www.linkedin.com/post/new/"
            )
        self.assertTrue(message.strip(), "manual mode said nothing at all")
        self.assertIn("publora", message.lower(), "manual mode does not mention the write layer")


if __name__ == "__main__":
    unittest.main()


class DeleteGuard(unittest.TestCase):
    """Publora's endpoint applies no status guard, so the client applies one.

    Deleting a group whose content is already live wipes the record, the media
    and the stats of a post that stays up on LinkedIn. The dashboard refuses it;
    the public API does not (publora/publora.com#478).
    """

    def client(self, status):
        from lib.publora_client import PubloraClient

        client = PubloraClient.__new__(PubloraClient)
        client.get_post = lambda *, post_group_id: {"postGroup": {"status": status}}
        client.BASE_URL = "https://example.invalid"
        client.timeout = 1
        return client

    def test_a_published_group_is_refused(self):
        from lib.publora_client import PubloraError

        for status in ("published", "partially_published"):
            with self.subTest(status=status), self.assertRaises(PubloraError) as caught:
                self.client(status).delete_post(post_group_id="abc")
            self.assertIn(status, str(caught.exception))
            self.assertIn("LinkedIn", str(caught.exception), "the refusal must say what to do instead")

    def test_a_draft_is_deleted(self):
        client = self.client("draft")
        sent = {}

        def record(url, **kwargs):
            sent["url"] = url
            return mock.Mock(status_code=200, json=lambda: {"success": True})

        client._session = mock.Mock()
        client._session.delete.side_effect = record
        self.assertEqual(client.delete_post(post_group_id="abc"), {"success": True})
        self.assertIn("/delete-post/abc", sent["url"])

    def test_the_guard_can_be_overridden_deliberately(self):
        """Dropping the record of a live post is sometimes what you mean. It
        just must not be the default."""
        client = self.client("published")
        client._session = mock.Mock()
        client._session.delete.return_value = mock.Mock(status_code=200, json=lambda: {"success": True})
        self.assertEqual(client.delete_post(post_group_id="abc", allow_live=True), {"success": True})


class PlatformIdResolution(unittest.TestCase):
    """The second Publora secret, derived rather than demanded.

    A key with no platform id behaves exactly like no key at all, and the id
    lives in a different corner of the dashboard from the key. It is derivable,
    so the bundle asks the API instead of asking the user.
    """

    def client(self, connections):
        from lib.publora_client import PubloraClient

        client = PubloraClient.__new__(PubloraClient)
        client.list_platform_connections = lambda: connections
        return client

    def test_one_linkedin_channel_resolves(self):
        resolved = self.client([
            {"platformId": "instagram-123"},
            {"platformId": "linkedin-abc"},
        ]).resolve_linkedin_platform_id()
        self.assertEqual(resolved, "linkedin-abc")

    def test_several_linkedin_channels_refuse_to_guess(self):
        """Picking one would publish to the wrong account. Ask instead."""
        resolved = self.client([
            {"platformId": "linkedin-abc"},
            {"platformId": "linkedin-xyz"},
        ]).resolve_linkedin_platform_id()
        self.assertIsNone(resolved)

    def test_no_linkedin_channel_resolves_to_nothing(self):
        self.assertIsNone(self.client([{"platformId": "threads-1"}]).resolve_linkedin_platform_id())

    def test_other_platforms_are_never_mistaken_for_linkedin(self):
        """A prefix match, not a substring one: `mylinkedin-` is not LinkedIn."""
        self.assertIsNone(self.client([{"platformId": "mylinkedin-abc"}]).resolve_linkedin_platform_id())
