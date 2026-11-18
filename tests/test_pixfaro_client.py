"""Offline tests for Pixfaro client behavior.

These tests protect the client-side contract around validation, caching,
force-refresh, and transient HTTP failures.

No credentials and no real Pixfaro network calls are used.
"""

from __future__ import annotations

import os
import unittest
import requests
from unittest.mock import Mock, patch

from lib.pixfaro_client import PixfaroClient, PixfaroError


def make_client() -> PixfaroClient:
    """Create a Pixfaro client using a temporary test environment variable."""
    with patch.dict(os.environ, {"PIXFARO_TOKEN": "test"}):
        return PixfaroClient()


class GenerateValidation(unittest.TestCase):
    """Invalid generation requests must fail before touching the network."""

    def setUp(self):
        self.client = make_client()

    @patch.object(PixfaroClient, "_post")
    def test_empty_prompt_is_rejected_before_calling(self, post):
        with self.assertRaises(PixfaroError):
            self.client.generate("   ")

        post.assert_not_called()

    @patch.object(PixfaroClient, "_post")
    def test_overlong_prompt_is_rejected_before_calling(self, post):
        with self.assertRaises(PixfaroError):
            self.client.generate("x" * 4001)

        post.assert_not_called()


class GenerateCache(unittest.TestCase):
    """Repeated identical generations should use the in-process cache."""

    def setUp(self):
        self.client = make_client()
        self.response = {
            "id": "img_123",
            "url": "https://media.example/image.png",
            "cost": 0.08,
        }

    @patch.object(PixfaroClient, "_post")
    def test_second_identical_generation_uses_cache(self, post):
        post.return_value = self.response

        first = self.client.generate("A data engineer at work")
        second = self.client.generate("A data engineer at work")

        self.assertEqual(first, self.response)
        self.assertEqual(second, self.response)

        post.assert_called_once_with(
            "/images/generations",
            {
                "model": "nano-banana-2",
                "prompt": "A data engineer at work",
                "aspect_ratio": "1:1",
                "resolution": "1K",
            },
        )

    @patch.object(PixfaroClient, "_post")
    def test_force_refresh_bypasses_cache(self, post):
        post.return_value = self.response

        self.client.generate("A data engineer at work")
        self.client.generate(
            "A data engineer at work",
            force_refresh=True,
        )

        self.assertEqual(post.call_count, 2)


class EditValidation(unittest.TestCase):
    """Edits must reference a real Pixfaro image id and instruction."""

    def setUp(self):
        self.client = make_client()

    @patch.object(PixfaroClient, "_post")
    def test_hosted_url_is_rejected_as_image_id(self, post):
        with self.assertRaises(PixfaroError):
            self.client.edit(
                "https://media.example/image.png",
                "Make the sky darker",
            )

        post.assert_not_called()

    @patch.object(PixfaroClient, "_post")
    def test_empty_instruction_is_rejected_before_calling(self, post):
        with self.assertRaises(PixfaroError):
            self.client.edit("img_123", "   ")

        post.assert_not_called()


class RetryBehaviour(unittest.TestCase):
    """Transient HTTP failures should be retried; client errors should not."""

    def setUp(self):
        self.client = make_client()

    @patch("lib.pixfaro_client.time.sleep")
    @patch.object(PixfaroClient, "_post")
    def test_rate_limit_is_retried(self, post, sleep):
        post.side_effect = [
            PixfaroError(
                "rate limited",
                status_code=429,
                retryable=True,
            ),
            {
                "id": "img_123",
                "url": "https://media.example/image.png",
            },
        ]

        result = self.client.generate("A data engineer at work")

        self.assertEqual(result["id"], "img_123")
        self.assertEqual(post.call_count, 2)
        sleep.assert_called_once()

    @patch("lib.pixfaro_client.time.sleep")
    def test_network_timeout_is_retried(self, sleep):
        post = Mock(
            side_effect=[
                requests.Timeout("simulated timeout"),
                Mock(
                    status_code=200,
                    json=Mock(return_value={
                        "id": "img_123",
                        "url": "https://media.example/image.png",
                    }),
                ),
            ]
        )
        self.client._session.post = post

        result = self.client.generate("A data engineer at work")

        self.assertEqual(result["id"], "img_123")
        self.assertEqual(post.call_count, 2)
        sleep.assert_called_once()

    @patch("lib.pixfaro_client.time.sleep")
    @patch.object(PixfaroClient, "_post")
    def test_bad_request_is_not_retried(self, post, sleep):
        post.side_effect = PixfaroError(
            "invalid request",
            status_code=400,
            retryable=False,
        )

        with self.assertRaises(PixfaroError):
            self.client.generate("A data engineer at work")

        post.assert_called_once()
        sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()