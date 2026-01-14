#!/usr/bin/env python3
"""
irc-topic-notify

Monitors an IRC channel topic for specific phrases and sends push notifications
via Pushover when detected.

Configuration via config.py (copy config.example.py and edit)

Usage:
    python irc_topic_notify.py              # Normal operation
    python irc_topic_notify.py --test       # Test Pushover notification
    python irc_topic_notify.py --test-trigger "Status: OPEN"  # Test trigger detection

https://github.com/ggfevans/irc-topic-notify
"""

from __future__ import annotations

__version__ = "1.0.0"

import argparse
import logging
import signal
import ssl
import sys
import threading
import time
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests
from irc.bot import SingleServerIRCBot
from irc.connection import Factory

# =============================================================================
# Configuration Loading
# =============================================================================

try:
    from config import (
        IRC_SERVER, IRC_PORT, IRC_CHANNEL, IRC_NICKNAME, IRC_REALNAME,
        TRIGGER_PHRASE,
        PUSHOVER_APP_TOKEN, PUSHOVER_USER_KEY,
        NOTIFICATION_TITLE, NOTIFICATION_MESSAGE, NOTIFICATION_URL, NOTIFICATION_URL_TITLE,
        NOTIFICATION_COOLDOWN_MINUTES, LOG_LEVEL
    )
    # Optional config with defaults
    try:
        from config import TRIGGER_CASE_SENSITIVE
    except ImportError:
        TRIGGER_CASE_SENSITIVE = True
    try:
        from config import HEALTH_PORT
    except ImportError:
        HEALTH_PORT = 8080
except ImportError:
    print("ERROR: config.py not found!")
    print("Copy config.example.py to config.py and add your Pushover tokens.")
    sys.exit(1)

# =============================================================================
# Logging Setup
# =============================================================================

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Global state for health checks
_bot_status: dict[str, any] = {"connected": False, "channel_joined": False}

# =============================================================================
# Utility Functions
# =============================================================================

def validate_config() -> None:
    """Validate configuration before starting."""
    errors: list[str] = []
    
    if not PUSHOVER_APP_TOKEN or 'your-' in PUSHOVER_APP_TOKEN.lower():
        errors.append("PUSHOVER_APP_TOKEN not configured")
    
    if not PUSHOVER_USER_KEY or 'your-' in PUSHOVER_USER_KEY.lower():
        errors.append("PUSHOVER_USER_KEY not configured")
    
    if not IRC_SERVER:
        errors.append("IRC_SERVER not configured")
    
    if not IRC_CHANNEL or not IRC_CHANNEL.startswith('#'):
        errors.append("IRC_CHANNEL must start with #")
    
    if errors:
        for e in errors:
            logger.error(f"Config error: {e}")
        logger.error("Edit config.py and fix the above errors.")
        sys.exit(1)
    
    logger.debug("Configuration validated successfully")


def send_pushover_notification(
    title: str | None = None,
    message: str | None = None,
    test: bool = False,
) -> bool:
    """Send Pushover notification. Returns True on success."""
    try:
        r = requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": PUSHOVER_APP_TOKEN,
                "user": PUSHOVER_USER_KEY,
                "message": message or NOTIFICATION_MESSAGE,
                "title": title or NOTIFICATION_TITLE,
                "priority": 0 if test else 1,  # Normal priority for tests
                "sound": "pushover" if test else "persistent",
                "url": NOTIFICATION_URL,
                "url_title": NOTIFICATION_URL_TITLE,
            },
            timeout=30
        )
        if r.status_code == 200:
            logger.info("✅ Pushover notification sent!")
            return True
        else:
            logger.error(f"Pushover error: {r.status_code} - {r.text}")
            return False
    except Exception as e:
        logger.error(f"Pushover error: {e}")
        return False


def check_trigger(topic_text: str) -> bool:
    """Check if topic contains trigger phrase.

    Case sensitivity controlled by TRIGGER_CASE_SENSITIVE in config.py.
    Defaults to case-sensitive matching to avoid false positives.
    """
    if TRIGGER_CASE_SENSITIVE:
        return TRIGGER_PHRASE in topic_text
    return TRIGGER_PHRASE.lower() in topic_text.lower()


# =============================================================================
# Health Check Server
# =============================================================================

class HealthHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for health checks."""

    def do_GET(self):
        if self.path == "/health" or self.path == "/":
            if _bot_status["channel_joined"]:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")
            else:
                self.send_response(503)
                self.end_headers()
                self.wfile.write(b"Not connected")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress request logging


def start_health_server(port: int) -> HTTPServer:
    """Start health check server in background thread."""
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info(f"Health server listening on port {port}")
    return server


# =============================================================================
# IRC Bot
# =============================================================================

class TopicMonitor(SingleServerIRCBot):
    """IRC Bot that monitors channel topic for specific phrases.

    IMPORTANT: This bot is READ-ONLY. It must NEVER send messages to the channel.
    Only permitted IRC commands: JOIN, NICK, QUIT.
    Do not add privmsg(), notice(), or action() calls.
    """

    channel: str
    last_notification: datetime | None
    current_topic: str | None
    _shutdown: bool

    def __init__(self) -> None:
        # Modern SSL context with proper hostname verification
        ssl_context = ssl.create_default_context()
        ssl_factory = Factory(
            wrapper=lambda sock: ssl_context.wrap_socket(sock, server_hostname=IRC_SERVER)
        )

        super().__init__(
            server_list=[(IRC_SERVER, IRC_PORT)],
            nickname=IRC_NICKNAME,
            realname=IRC_REALNAME,
            connect_factory=ssl_factory
        )

        self.channel = IRC_CHANNEL
        self.last_notification = None
        self.current_topic = None
        self._shutdown = False
        logger.info(f"Bot initialized for {IRC_SERVER}:{IRC_PORT} {IRC_CHANNEL}")
    
    def on_welcome(self, connection, event):
        """Connected to server."""
        _bot_status["connected"] = True
        logger.info(f"Connected to {IRC_SERVER}. Joining {self.channel}...")
        connection.join(self.channel)
    
    def on_nicknameinuse(self, connection, event):
        """Nickname is taken - try alternative."""
        new_nick = connection.get_nickname() + "_"
        logger.warning(f"Nickname in use, trying {new_nick}")
        connection.nick(new_nick)
    
    def on_join(self, connection, event):
        """Joined channel."""
        if event.source.nick == connection.get_nickname():
            _bot_status["channel_joined"] = True
            logger.info(f"Successfully joined {self.channel}")
    
    def on_currenttopic(self, connection, event):
        """Current topic on join (RPL_TOPIC 332)."""
        topic = event.arguments[1] if len(event.arguments) > 1 else ""
        logger.info(f"Current topic ({len(topic)} chars): {topic[:100]}{'...' if len(topic) > 100 else ''}")
        logger.debug(f"Full topic: {topic}")
        self.current_topic = topic
        self._check_topic(topic, is_change=False)
    
    def on_topic(self, connection, event):
        """Topic changed."""
        new_topic = event.arguments[0] if event.arguments else ""
        changer = event.source.nick if event.source else "Unknown"
        
        logger.info(f"Topic changed by {changer} ({len(new_topic)} chars): {new_topic[:100]}{'...' if len(new_topic) > 100 else ''}")
        logger.debug(f"Full new topic: {new_topic}")
        
        if new_topic != self.current_topic:
            self.current_topic = new_topic
            self._check_topic(new_topic, is_change=True)
    
    def _check_topic(self, topic: str, is_change: bool = False) -> None:
        """Check if topic contains trigger phrase."""
        if check_trigger(topic):
            logger.warning(f"🎉 TRIGGER DETECTED: '{TRIGGER_PHRASE}'")
            
            if self._should_notify():
                if send_pushover_notification():
                    self.last_notification = datetime.now()
            else:
                cooldown_remaining = (
                    self.last_notification + timedelta(minutes=NOTIFICATION_COOLDOWN_MINUTES) 
                    - datetime.now()
                )
                logger.info(f"Notification skipped (cooldown: {cooldown_remaining.seconds}s remaining)")
        else:
            logger.debug("Trigger phrase not found in topic")
    
    def _should_notify(self) -> bool:
        """Check if cooldown has elapsed."""
        if self.last_notification is None:
            return True
        cooldown = timedelta(minutes=NOTIFICATION_COOLDOWN_MINUTES)
        return datetime.now() - self.last_notification > cooldown
    
    def on_disconnect(self, connection, event):
        """Disconnected from server."""
        _bot_status["connected"] = False
        _bot_status["channel_joined"] = False
        if self._shutdown:
            logger.info("Disconnected (shutdown requested)")
        else:
            logger.warning("Disconnected from server. Will attempt reconnect...")
    
    def on_kick(self, connection, event):
        """Kicked from channel."""
        kicked_nick = event.arguments[0] if event.arguments else ""
        if kicked_nick == connection.get_nickname():
            _bot_status["channel_joined"] = False
            logger.warning(f"Kicked from {self.channel}. Rejoining in 30s...")
            time.sleep(30)
            connection.join(self.channel)
    
    def on_error(self, connection, event):
        """IRC protocol error."""
        logger.error(f"IRC error: {event.arguments}")
    
    def shutdown(self) -> None:
        """Graceful shutdown."""
        self._shutdown = True
        logger.info("Shutdown requested, disconnecting...")
        self.die("Shutting down")


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(description="IRC Topic Notify - monitor channel topics and get push notifications")
    parser.add_argument('--test', action='store_true', 
                        help="Send test notification and exit")
    parser.add_argument('--test-trigger', metavar='TOPIC',
                        help="Test trigger detection against provided topic text")
    args = parser.parse_args()
    
    # Always validate config
    validate_config()
    
    # Test mode: send notification and exit
    if args.test:
        logger.info("Sending test notification...")
        success = send_pushover_notification(
            title="IRC Monitor Test",
            message="✅ Test notification - Pushover is working!",
            test=True
        )
        sys.exit(0 if success else 1)
    
    # Test trigger detection
    if args.test_trigger:
        logger.info(f"Testing trigger detection against: {args.test_trigger}")
        if check_trigger(args.test_trigger):
            logger.info(f"✅ WOULD TRIGGER - phrase '{TRIGGER_PHRASE}' found")
        else:
            logger.info(f"❌ Would NOT trigger - phrase '{TRIGGER_PHRASE}' not found")
        sys.exit(0)
    
    # Normal operation
    logger.info("=" * 50)
    logger.info("irc-topic-notify")
    logger.info(f"Server: {IRC_SERVER}:{IRC_PORT}")
    logger.info(f"Channel: {IRC_CHANNEL}")
    logger.info(f"Trigger: '{TRIGGER_PHRASE}'")
    logger.info(f"Cooldown: {NOTIFICATION_COOLDOWN_MINUTES} minutes")
    logger.info("=" * 50)

    # Start health check server
    health_server = start_health_server(HEALTH_PORT)
    
    bot = TopicMonitor()
    
    # Handle SIGTERM gracefully (systemd sends this)
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}")
        bot.shutdown()
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Run with auto-reconnect
    while not bot._shutdown:
        try:
            bot.start()
        except KeyboardInterrupt:
            bot.shutdown()
            break
        except SystemExit:
            break
        except Exception as e:
            if bot._shutdown:
                break
            logger.error(f"Bot error: {e}")
            logger.info("Restarting in 60s...")
            time.sleep(60)
    
    logger.info("Goodbye!")


if __name__ == "__main__":
    main()
