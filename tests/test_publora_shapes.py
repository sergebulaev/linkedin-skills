"""The fields we read back from Publora must be the ones it actually returns.

The fixture is a real `GET /get-post` response for a published post that carried
a generated image, recorded live and redacted.

It exists because the field is `media`, not `mediaFiles` — and reading the
plausible-but-wrong name made a working image pipeline look broken all the way
up to "the image did not attach", on a post where the image was plainly there.
Apify fixtures already cover the read layer; this covers the write layer.

Offline. No credentials, no network.
"""
from __future__ import annotations

import json
import pathlib
import unittest

FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"
POST = json.loads((FIXTURES / "publora_get_post.json").read_text(encoding="utf-8"))


class PostGroupShape(unittest.TestCase):
    """What `get_post` answers, and what a caller may rely on."""

    def test_status_is_top_level(self):
        """Not nested under a `postGroup` key, whatever the dashboard shows."""
        self.assertIn("status", POST)
        self.assertEqual(POST["status"], "published")

    def test_the_live_statuses_the_delete_guard_watches_for_are_real(self):
        """`delete_post` refuses these. A typo there would silently disarm it."""
        from lib.publora_client import PubloraClient

        self.assertIn(POST["status"], PubloraClient.LIVE_STATUSES + ("draft", "scheduled", "failed"))
        self.assertIn("published", PubloraClient.LIVE_STATUSES)
        self.assertIn("partially_published", PubloraClient.LIVE_STATUSES)

    def test_platforms_are_id_strings(self):
        """create_post normalises dicts to these strings; the response confirms
        the shape the API settled on."""
        self.assertIsInstance(POST["platforms"], list)
        for entry in POST["platforms"]:
            self.assertIsInstance(entry, str, "a platform came back as something other than an id")


class MediaShape(unittest.TestCase):
    """The Pixfaro handover: a hosted URL goes in, Publora fetches it, and the
    post carries its own copy."""

    def test_the_field_is_called_media(self):
        self.assertIn("media", POST, f"no `media`; the response has {sorted(POST)}")
        self.assertNotIn("mediaFiles", POST, "if this ever appears, update the readers too")

    def test_an_attached_image_is_present_and_ready(self):
        media = POST["media"]
        self.assertTrue(media, "the fixture must carry an attachment or it proves nothing")
        item = media[0]
        self.assertEqual(item["type"], "image")
        self.assertEqual(item["status"], "ready",
                         f"attachment not ready: {item.get('failureReason')}")
        self.assertIsNone(item["failureReason"])

    def test_publora_rehosts_the_file(self):
        """It downloads server-side rather than hot-linking, so a Pixfaro URL
        expiring later cannot break a published post."""
        item = POST["media"][0]
        self.assertTrue(item["url"].startswith("https://media.publora.com/"), item["url"])
        self.assertTrue(item["sourceFileName"], "the original filename is the audit trail")

    def test_failure_would_be_visible(self):
        """`status` and `failureReason` are the fields to report on, so a future
        broken upload reads as broken instead of as an empty list."""
        for key in ("status", "failureReason", "mediaId"):
            self.assertIn(key, POST["media"][0])


class ChildPostShape(unittest.TestCase):
    """One child per platform. This is where the published id lives."""

    def setUp(self):
        self.child = POST["posts"][0]

    def test_the_published_id_is_a_share_urn(self):
        """`lib.repost` needs a share urn, and CLAUDE.md forbids hand-converting
        an activity id into one. This is where a real one comes from."""
        self.assertEqual(self.child["status"], "published")
        self.assertTrue(self.child["postedId"].startswith("urn:li:share:"), self.child["postedId"])

    def test_permalink_is_not_populated(self):
        """It is present but null, so the post URL has to be built from the
        share urn. Pinned so nobody reports "no link" when there is an id."""
        self.assertIn("permalink", self.child)
        self.assertIsNone(self.child["permalink"])

    def test_a_url_can_be_built_from_the_id(self):
        url = f"https://www.linkedin.com/feed/update/{self.child['postedId']}/"
        self.assertIn("urn:li:share:", url)

    def test_errors_would_be_reportable(self):
        self.assertIn("error", self.child)
        self.assertIsNone(self.child["error"], "the fixture should be a clean publish")


if __name__ == "__main__":
    unittest.main()
