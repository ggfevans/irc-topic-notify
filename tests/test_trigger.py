"""Tests for trigger phrase detection."""

from __future__ import annotations

from unittest.mock import patch

import pytest


class TestCheckTrigger:
    """Tests for the check_trigger function."""

    def test_trigger_found_exact_match(self, patch_config):
        """Trigger phrase is found when it matches exactly."""
        import irc_topic_notify

        assert irc_topic_notify.check_trigger("Server: ONLINE") is True

    def test_trigger_found_at_start(self, patch_config):
        """Trigger phrase is found at the start of topic."""
        import irc_topic_notify

        assert irc_topic_notify.check_trigger("ONLINE - all systems go") is True

    def test_trigger_found_at_end(self, patch_config):
        """Trigger phrase is found at the end of topic."""
        import irc_topic_notify

        assert irc_topic_notify.check_trigger("Server is now ONLINE") is True

    def test_trigger_not_found(self, patch_config):
        """Trigger phrase is not found when absent."""
        import irc_topic_notify

        assert irc_topic_notify.check_trigger("Server: OFFLINE") is False

    def test_trigger_case_sensitive_no_match(self, patch_config):
        """Case-sensitive mode doesn't match different case."""
        import irc_topic_notify

        # TRIGGER_PHRASE is "ONLINE", should not match "online"
        assert irc_topic_notify.check_trigger("Server: online") is False

    def test_trigger_case_sensitive_partial_match(self, patch_config):
        """Case-sensitive mode doesn't match partial case differences."""
        import irc_topic_notify

        assert irc_topic_notify.check_trigger("Server: Online") is False

    def test_trigger_empty_topic(self, patch_config):
        """Empty topic doesn't trigger."""
        import irc_topic_notify

        assert irc_topic_notify.check_trigger("") is False

    def test_trigger_phrase_only(self, patch_config):
        """Topic containing only the trigger phrase matches."""
        import irc_topic_notify

        assert irc_topic_notify.check_trigger("ONLINE") is True


class TestCheckTriggerCaseInsensitive:
    """Tests for case-insensitive trigger matching."""

    def test_trigger_lowercase_matches(self, patch_config):
        """Lowercase trigger phrase matches in case-insensitive mode."""
        import irc_topic_notify

        irc_topic_notify.TRIGGER_CASE_SENSITIVE = False
        assert irc_topic_notify.check_trigger("Server: online") is True

    def test_trigger_mixed_case_matches(self, patch_config):
        """Mixed case trigger phrase matches in case-insensitive mode."""
        import irc_topic_notify

        irc_topic_notify.TRIGGER_CASE_SENSITIVE = False
        assert irc_topic_notify.check_trigger("Server: Online Now") is True

    def test_trigger_uppercase_still_matches(self, patch_config):
        """Uppercase still matches in case-insensitive mode."""
        import irc_topic_notify

        irc_topic_notify.TRIGGER_CASE_SENSITIVE = False
        assert irc_topic_notify.check_trigger("Server: ONLINE") is True

    def test_trigger_not_found_still_fails(self, patch_config):
        """Non-matching text still fails in case-insensitive mode."""
        import irc_topic_notify

        irc_topic_notify.TRIGGER_CASE_SENSITIVE = False
        assert irc_topic_notify.check_trigger("Server: OFFLINE") is False


class TestTriggerEdgeCases:
    """Edge case tests for trigger detection."""

    def test_trigger_with_unicode(self, patch_config):
        """Trigger works with unicode in topic."""
        import irc_topic_notify

        assert irc_topic_notify.check_trigger("🟢 ONLINE 🟢") is True

    def test_trigger_with_special_chars(self, patch_config):
        """Trigger works with special characters around it."""
        import irc_topic_notify

        assert irc_topic_notify.check_trigger("[STATUS] ONLINE!!!") is True

    def test_trigger_substring_matches(self, patch_config):
        """Trigger matches as substring (e.g., ONLINEMODE contains ONLINE)."""
        import irc_topic_notify

        # This is expected behaviour - substring matching
        assert irc_topic_notify.check_trigger("ONLINEMODE enabled") is True

    def test_trigger_very_long_topic(self, patch_config):
        """Trigger works in very long topics."""
        import irc_topic_notify

        long_topic = "x" * 1000 + " ONLINE " + "y" * 1000
        assert irc_topic_notify.check_trigger(long_topic) is True

    def test_trigger_whitespace_only(self, patch_config):
        """Whitespace-only topic doesn't trigger."""
        import irc_topic_notify

        assert irc_topic_notify.check_trigger("   \t\n  ") is False
