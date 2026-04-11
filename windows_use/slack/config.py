"""
Slack integration configuration.

This module contains configuration constants and defaults for Slack integration.
"""

# Default Slack configuration
DEFAULT_CHANNEL = "#windows-use-agent"
DEFAULT_USERNAME = "Windows-Use Agent"
DEFAULT_ICON_EMOJI = ":robot_face:"

# Event notification settings
NOTIFY_AGENT_START = True
NOTIFY_AGENT_COMPLETE = True
NOTIFY_TOOL_EXECUTION = True
NOTIFY_UI_EVENTS = False  # Can be verbose, disabled by default
NOTIFY_ERRORS = True

# Message formatting
MAX_MESSAGE_LENGTH = 3000  # Slack's limit is 40000 but keep it reasonable
MAX_FIELD_LENGTH = 1000
TRUNCATE_SUFFIX = "... (truncated)"

# Rate limiting
MIN_NOTIFICATION_INTERVAL = 1.0  # Minimum seconds between notifications

# Environment variable names
ENV_SLACK_WEBHOOK_URL = "SLACK_WEBHOOK_URL"
ENV_SLACK_BOT_TOKEN = "SLACK_BOT_TOKEN"
ENV_SLACK_CHANNEL = "SLACK_CHANNEL"
ENV_SLACK_ENABLED = "SLACK_NOTIFICATIONS_ENABLED"

# Message colors
COLOR_SUCCESS = "#36a64f"  # Green
COLOR_ERROR = "#ff0000"    # Red
COLOR_WARNING = "#ff9900"  # Orange
COLOR_INFO = "#0066cc"     # Blue
COLOR_NEUTRAL = "#808080"  # Gray

# Emoji indicators
EMOJI_SUCCESS = ":white_check_mark:"
EMOJI_ERROR = ":x:"
EMOJI_WARNING = ":warning:"
EMOJI_INFO = ":information_source:"
EMOJI_TOOL = ":wrench:"
EMOJI_AGENT = ":robot_face:"
EMOJI_UI_EVENT = ":desktop_computer:"
EMOJI_FOCUS = ":dart:"
EMOJI_STRUCTURE = ":building_construction:"
EMOJI_PROPERTY = ":gear:"
