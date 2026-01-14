"""Tests for the TopicMonitor IRC bot class."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest


class TestTopicMonitorInit:
    """Tests for TopicMonitor initialization."""

    def test_bot_initializes_with_correct_channel(self, patch_config):
        """Bot initializes with the configured channel."""
        import irc_topic_notify

        bot = irc_topic_notify.TopicMonitor()

        assert bot.channel == "#test-channel"

    def test_bot_starts_with_no_last_notification(self, patch_config):
        """Bot starts with no previous notification time."""
        import irc_topic_notify

        bot = irc_topic_notify.TopicMonitor()

        assert bot.last_notification is None

    def test_bot_starts_with_no_current_topic(self, patch_config):
        """Bot starts with no current topic."""
        import irc_topic_notify

        bot = irc_topic_notify.TopicMonitor()

        assert bot.current_topic is None

    def test_bot_starts_not_shutdown(self, patch_config):
        """Bot starts with shutdown flag False."""
        import irc_topic_notify

        bot = irc_topic_notify.TopicMonitor()

        assert bot._shutdown is False


class TestShouldNotify:
    """Tests for the _should_notify method."""

    def test_should_notify_when_never_notified(self, patch_config):
        """Should notify when no previous notification exists."""
        import irc_topic_notify

        bot = irc_topic_notify.TopicMonitor()
        bot.last_notification = None

        assert bot._should_notify() is True

    def test_should_notify_after_cooldown_elapsed(self, patch_config):
        """Should notify after cooldown period has elapsed."""
        import irc_topic_notify

        bot = irc_topic_notify.TopicMonitor()
        # Set last notification to 31 minutes ago (cooldown is 30)
        bot.last_notification = datetime.now() - timedelta(minutes=31)

        assert bot._should_notify() is True

    def test_should_not_notify_during_cooldown(self, patch_config):
        """Should not notify during cooldown period."""
        import irc_topic_notify

        bot = irc_topic_notify.TopicMonitor()
        # Set last notification to 10 minutes ago (cooldown is 30)
        bot.last_notification = datetime.now() - timedelta(minutes=10)

        assert bot._should_notify() is False

    def test_should_notify_exactly_at_cooldown(self, patch_config):
        """Should notify when exactly at cooldown boundary."""
        import irc_topic_notify

        bot = irc_topic_notify.TopicMonitor()
        # Set last notification to just over 30 minutes ago
        bot.last_notification = datetime.now() - timedelta(minutes=30, seconds=1)

        assert bot._should_notify() is True


class TestCheckTopic:
    """Tests for the _check_topic method."""

    def test_check_topic_triggers_notification(self, mock_requests_post):
        """Trigger phrase in topic causes notification."""
        import irc_topic_notify

        bot = irc_topic_notify.TopicMonitor()
        bot.last_notification = None

        bot._check_topic("Server: ONLINE")

        mock_requests_post.assert_called_once()
        assert bot.last_notification is not None

    def test_check_topic_no_trigger_no_notification(self, mock_requests_post):
        """No trigger phrase means no notification."""
        import irc_topic_notify

        bot = irc_topic_notify.TopicMonitor()
        bot._check_topic("Server: OFFLINE")

        mock_requests_post.assert_not_called()

    def test_check_topic_respects_cooldown(self, mock_requests_post):
        """Notification respects cooldown period."""
        import irc_topic_notify

        bot = irc_topic_notify.TopicMonitor()
        bot.last_notification = datetime.now() - timedelta(minutes=5)

        bot._check_topic("Server: ONLINE")

        mock_requests_post.assert_not_called()

    def test_check_topic_updates_last_notification_on_success(self, mock_requests_post):
        """Successful notification updates last_notification timestamp."""
        import irc_topic_notify

        bot = irc_topic_notify.TopicMonitor()
        bot.last_notification = None
        before = datetime.now()

        bot._check_topic("Server: ONLINE")

        assert bot.last_notification is not None
        assert bot.last_notification >= before

    def test_check_topic_does_not_update_on_failure(self, patch_config):
        """Failed notification doesn't update last_notification."""
        import irc_topic_notify

        with patch.object(irc_topic_notify.requests, "post") as mock_post:
            mock_post.return_value = MagicMock(status_code=500, text="error")

            bot = irc_topic_notify.TopicMonitor()
            bot.last_notification = None

            bot._check_topic("Server: ONLINE")

            assert bot.last_notification is None


class TestShutdown:
    """Tests for the shutdown method."""

    def test_shutdown_sets_flag(self, patch_config):
        """Shutdown sets the _shutdown flag."""
        import irc_topic_notify

        bot = irc_topic_notify.TopicMonitor()

        # Mock the die method since it comes from the mocked parent class
        bot.die = MagicMock()
        bot.shutdown()

        assert bot._shutdown is True
        bot.die.assert_called_once_with("Shutting down")
