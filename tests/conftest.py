"""Pytest configuration and fixtures for irc-topic-notify tests."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# Add parent directory to path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent))


# Mock the irc module before any test imports irc_topic_notify
@pytest.fixture(scope="session", autouse=True)
def mock_irc_module():
    """Mock the irc module globally for all tests."""
    mock_irc = MagicMock()
    mock_irc.bot.SingleServerIRCBot = MagicMock
    mock_irc.connection.Factory = MagicMock
    sys.modules["irc"] = mock_irc
    sys.modules["irc.bot"] = mock_irc.bot
    sys.modules["irc.connection"] = mock_irc.connection
    yield mock_irc


@pytest.fixture
def mock_config_values() -> dict[str, Any]:
    """Return a valid mock configuration dictionary."""
    return {
        "IRC_SERVER": "irc.example.com",
        "IRC_PORT": 6697,
        "IRC_CHANNEL": "#test-channel",
        "IRC_NICKNAME": "TestBot",
        "IRC_REALNAME": "Test Bot",
        "TRIGGER_PHRASE": "ONLINE",
        "TRIGGER_CASE_SENSITIVE": True,
        "PUSHOVER_APP_TOKEN": "abc123token",
        "PUSHOVER_USER_KEY": "xyz789user",
        "NOTIFICATION_TITLE": "Test Alert",
        "NOTIFICATION_MESSAGE": "Test message",
        "NOTIFICATION_URL": "https://example.com",
        "NOTIFICATION_URL_TITLE": "Click here",
        "NOTIFICATION_COOLDOWN_MINUTES": 30,
        "LOG_LEVEL": "INFO",
    }


@pytest.fixture
def patch_config(mock_config_values: dict[str, Any], mock_irc_module):
    """Patch the config module with mock values before importing irc_topic_notify."""
    # Create a mock config module
    mock_config = MagicMock()
    for key, value in mock_config_values.items():
        setattr(mock_config, key, value)

    # Add config to sys.modules before importing irc_topic_notify
    sys.modules["config"] = mock_config

    # Now we need to reload irc_topic_notify to pick up the mocked config
    # First remove it if it was already imported
    if "irc_topic_notify" in sys.modules:
        del sys.modules["irc_topic_notify"]

    # Import fresh with mocked dependencies
    import irc_topic_notify

    # Patch the module-level variables
    for key, value in mock_config_values.items():
        if hasattr(irc_topic_notify, key):
            setattr(irc_topic_notify, key, value)

    yield mock_config_values

    # Cleanup
    if "config" in sys.modules:
        del sys.modules["config"]
    if "irc_topic_notify" in sys.modules:
        del sys.modules["irc_topic_notify"]


@pytest.fixture
def mock_requests_post(patch_config):
    """Mock requests.post for Pushover API calls."""
    import irc_topic_notify

    with patch.object(irc_topic_notify.requests, "post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"status":1}'
        mock_post.return_value = mock_response
        yield mock_post


@pytest.fixture
def mock_requests_post_failure(patch_config):
    """Mock requests.post to simulate Pushover API failure."""
    import irc_topic_notify

    with patch.object(irc_topic_notify.requests, "post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = '{"errors":["invalid token"]}'
        mock_post.return_value = mock_response
        yield mock_post
