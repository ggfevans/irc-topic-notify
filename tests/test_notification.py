"""Tests for Pushover notification functionality."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestSendPushoverNotification:
    """Tests for the send_pushover_notification function."""

    def test_successful_notification(self, mock_requests_post):
        """Successful notification returns True."""
        import irc_topic_notify

        result = irc_topic_notify.send_pushover_notification()

        assert result is True
        mock_requests_post.assert_called_once()

    def test_notification_sends_correct_data(self, mock_requests_post):
        """Notification sends correct data to Pushover API."""
        import irc_topic_notify

        irc_topic_notify.send_pushover_notification()

        call_args = mock_requests_post.call_args
        assert call_args[0][0] == "https://api.pushover.net/1/messages.json"

        data = call_args[1]["data"]
        assert data["token"] == "abc123token"
        assert data["user"] == "xyz789user"
        assert data["title"] == "Test Alert"
        assert data["message"] == "Test message"

    def test_custom_title_and_message(self, mock_requests_post):
        """Custom title and message override defaults."""
        import irc_topic_notify

        irc_topic_notify.send_pushover_notification(title="Custom Title", message="Custom Message")

        data = mock_requests_post.call_args[1]["data"]
        assert data["title"] == "Custom Title"
        assert data["message"] == "Custom Message"

    def test_test_mode_uses_normal_priority(self, mock_requests_post):
        """Test mode uses normal priority (0) instead of high (1)."""
        import irc_topic_notify

        irc_topic_notify.send_pushover_notification(test=True)

        data = mock_requests_post.call_args[1]["data"]
        assert data["priority"] == 0
        assert data["sound"] == "pushover"

    def test_normal_mode_uses_high_priority(self, mock_requests_post):
        """Normal mode uses high priority (1)."""
        import irc_topic_notify

        irc_topic_notify.send_pushover_notification(test=False)

        data = mock_requests_post.call_args[1]["data"]
        assert data["priority"] == 1
        assert data["sound"] == "persistent"

    def test_failed_notification_returns_false(self, mock_requests_post_failure):
        """Failed notification (non-200 status) returns False."""
        import irc_topic_notify

        result = irc_topic_notify.send_pushover_notification()

        assert result is False

    def test_network_error_returns_false(self, patch_config):
        """Network error returns False and doesn't raise."""
        import irc_topic_notify

        with patch.object(irc_topic_notify.requests, "post") as mock_post:
            mock_post.side_effect = Exception("Connection refused")

            result = irc_topic_notify.send_pushover_notification()

            assert result is False

    def test_timeout_is_set(self, mock_requests_post):
        """Request includes a timeout."""
        import irc_topic_notify

        irc_topic_notify.send_pushover_notification()

        call_args = mock_requests_post.call_args
        assert call_args[1]["timeout"] == 30

    def test_url_included_in_notification(self, mock_requests_post):
        """URL and URL title are included in notification."""
        import irc_topic_notify

        irc_topic_notify.send_pushover_notification()

        data = mock_requests_post.call_args[1]["data"]
        assert data["url"] == "https://example.com"
        assert data["url_title"] == "Click here"
