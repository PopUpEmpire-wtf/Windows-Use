"""
Slack integration module for Windows-Use agent.

Provides Slack notification capabilities for agent events, tool executions,
and UI state changes.
"""

from windows_use.slack.service import SlackIntegration
from windows_use.slack.views import SlackNotificationConfig, SlackMessage
from windows_use.slack.formatter import (
    format_agent_start,
    format_agent_step,
    format_agent_complete,
    format_tool_execution,
    format_ui_event_focus,
    format_ui_event_structure,
    format_ui_event_property,
    format_error,
    format_custom_message,
)

__all__ = [
    "SlackIntegration",
    "SlackNotificationConfig",
    "SlackMessage",
    "format_agent_start",
    "format_agent_step",
    "format_agent_complete",
    "format_tool_execution",
    "format_ui_event_focus",
    "format_ui_event_structure",
    "format_ui_event_property",
    "format_error",
    "format_custom_message",
]
