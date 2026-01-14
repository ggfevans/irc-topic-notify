"""Tests for configuration validation."""

from __future__ import annotations

import pytest


class TestValidateConfig:
    """Tests for the validate_config function."""

    def test_valid_config_passes(self, patch_config):
        """Valid configuration passes validation without error."""
        import irc_topic_notify

        # Should not raise or exit
        irc_topic_notify.validate_config()

    def test_missing_pushover_app_token_exits(self, patch_config):
        """Missing Pushover app token causes exit."""
        import irc_topic_notify

        irc_topic_notify.PUSHOVER_APP_TOKEN = "your-app-token-here"
        with pytest.raises(SystemExit) as exc_info:
            irc_topic_notify.validate_config()
        assert exc_info.value.code == 1

    def test_missing_pushover_user_key_exits(self, patch_config):
        """Missing Pushover user key causes exit."""
        import irc_topic_notify

        irc_topic_notify.PUSHOVER_USER_KEY = "your-user-key-here"
        with pytest.raises(SystemExit) as exc_info:
            irc_topic_notify.validate_config()
        assert exc_info.value.code == 1

    def test_empty_pushover_app_token_exits(self, patch_config):
        """Empty Pushover app token causes exit."""
        import irc_topic_notify

        irc_topic_notify.PUSHOVER_APP_TOKEN = ""
        with pytest.raises(SystemExit) as exc_info:
            irc_topic_notify.validate_config()
        assert exc_info.value.code == 1

    def test_empty_irc_server_exits(self, patch_config):
        """Empty IRC server causes exit."""
        import irc_topic_notify

        irc_topic_notify.IRC_SERVER = ""
        with pytest.raises(SystemExit) as exc_info:
            irc_topic_notify.validate_config()
        assert exc_info.value.code == 1

    def test_channel_without_hash_exits(self, patch_config):
        """IRC channel without # prefix causes exit."""
        import irc_topic_notify

        irc_topic_notify.IRC_CHANNEL = "test-channel"
        with pytest.raises(SystemExit) as exc_info:
            irc_topic_notify.validate_config()
        assert exc_info.value.code == 1

    def test_channel_with_hash_passes(self, patch_config):
        """IRC channel with # prefix passes validation."""
        import irc_topic_notify

        irc_topic_notify.IRC_CHANNEL = "#valid-channel"
        # Should not raise
        irc_topic_notify.validate_config()

    def test_multiple_errors_all_reported(self, patch_config, caplog):
        """Multiple config errors are all logged before exit."""
        import irc_topic_notify

        irc_topic_notify.PUSHOVER_APP_TOKEN = ""
        irc_topic_notify.PUSHOVER_USER_KEY = ""
        irc_topic_notify.IRC_SERVER = ""

        with pytest.raises(SystemExit):
            irc_topic_notify.validate_config()

        # Check that multiple errors were logged
        error_messages = [r.message for r in caplog.records if r.levelname == "ERROR"]
        assert len(error_messages) >= 3
