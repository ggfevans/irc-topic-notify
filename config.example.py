# IRC Topic Notify - Configuration
# Copy this file to config.py and edit with your values

# =============================================================================
# IRC Settings
# =============================================================================
# Server to connect to (must support SSL on the specified port)
IRC_SERVER = "irc.libera.chat"
IRC_PORT = 6697  # SSL port (usually 6697 or 7000)
IRC_CHANNEL = "#your-channel"
IRC_NICKNAME = "TopicWatcher"  # Change to something unique
IRC_REALNAME = "Topic Monitor Bot"

# =============================================================================
# Trigger Settings
# =============================================================================
# Phrase to watch for in topic
# Examples:
#   "ONLINE" - game server back up
#   "INCIDENT" - ops channel alert
#   "LIVE NOW" - stream starting
#   "🟢" - emoji-based status indicators work too
TRIGGER_PHRASE = "ONLINE"

# Case-sensitive matching (default: True)
# Set to False if you want "online", "ONLINE", and "Online" to all trigger
TRIGGER_CASE_SENSITIVE = True

# =============================================================================
# Pushover Notification Settings
# =============================================================================
# Get these from https://pushover.net
# 1. Create an app at pushover.net/apps/build → gives you APP_TOKEN
# 2. Your USER_KEY is on your Pushover dashboard
PUSHOVER_APP_TOKEN = "your-app-token-here"
PUSHOVER_USER_KEY = "your-user-key-here"

# Notification content (customize for your use case)
NOTIFICATION_TITLE = "IRC Topic Alert"
NOTIFICATION_MESSAGE = "🔔 Topic trigger detected!\n\nCheck the channel for details."
NOTIFICATION_URL = ""  # Optional: URL to include in notification
NOTIFICATION_URL_TITLE = "Open Link"  # Button text for the URL

# =============================================================================
# Behavior Settings
# =============================================================================
# Prevent notification spam if topic changes multiple times quickly
NOTIFICATION_COOLDOWN_MINUTES = 30

# Logging level: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL = "INFO"
