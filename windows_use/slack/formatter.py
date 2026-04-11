"""
Slack message formatting utilities.

This module provides functions to format agent data, events, and results
into rich Slack messages with attachments and blocks.
"""

from windows_use.slack.views import SlackMessage, SlackAttachment, SlackField, SlackBlock
from windows_use.slack.config import (
    COLOR_SUCCESS,
    COLOR_ERROR,
    COLOR_INFO,
    COLOR_WARNING,
    EMOJI_SUCCESS,
    EMOJI_ERROR,
    EMOJI_AGENT,
    EMOJI_TOOL,
    EMOJI_UI_EVENT,
    EMOJI_FOCUS,
    EMOJI_STRUCTURE,
    EMOJI_PROPERTY,
    MAX_MESSAGE_LENGTH,
    MAX_FIELD_LENGTH,
    TRUNCATE_SUFFIX,
)
from datetime import datetime
import json


def truncate_text(text: str, max_length: int = MAX_FIELD_LENGTH) -> str:
    """Truncate text to maximum length with suffix."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(TRUNCATE_SUFFIX)] + TRUNCATE_SUFFIX


def format_agent_start(query: str, max_steps: int, model: str, provider: str) -> SlackMessage:
    """Format agent start notification."""
    text = f"{EMOJI_AGENT} *Agent Started*"

    attachment = SlackAttachment(
        fallback=f"Agent started: {query}",
        color=COLOR_INFO,
        title="New Agent Task",
        text=truncate_text(query, MAX_MESSAGE_LENGTH),
        fields=[
            SlackField(title="Model", value=model, short=True),
            SlackField(title="Provider", value=provider, short=True),
            SlackField(title="Max Steps", value=str(max_steps), short=True),
            SlackField(
                title="Started", value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), short=True
            ),
        ],
        footer="Windows-Use Agent",
    )

    return SlackMessage(text=text, attachments=[attachment])


def format_agent_step(
    step: int, max_steps: int, thought: str | None, action_name: str | None
) -> SlackMessage:
    """Format agent step notification."""
    text = f"{EMOJI_AGENT} Step {step}/{max_steps}"

    fields = [SlackField(title="Step", value=f"{step}/{max_steps}", short=True)]

    if thought:
        fields.append(SlackField(title="Thought", value=truncate_text(thought), short=False))

    if action_name:
        fields.append(SlackField(title="Action", value=action_name, short=True))

    attachment = SlackAttachment(
        fallback=f"Agent step {step}/{max_steps}",
        color=COLOR_INFO,
        fields=fields,
        footer="Windows-Use Agent",
    )

    return SlackMessage(text=text, attachments=[attachment])


def format_tool_execution(
    tool_name: str, params: dict, result: str, is_success: bool
) -> SlackMessage:
    """Format tool execution notification."""
    color = COLOR_SUCCESS if is_success else COLOR_ERROR
    emoji = EMOJI_SUCCESS if is_success else EMOJI_ERROR
    status = "Success" if is_success else "Failed"

    text = f"{EMOJI_TOOL} Tool: `{tool_name}` - {emoji} {status}"

    fields = [SlackField(title="Tool", value=tool_name, short=True)]

    if params:
        # Format params as JSON for readability
        params_str = json.dumps(params, indent=2)
        fields.append(SlackField(title="Parameters", value=f"```{params_str}```", short=False))

    if result:
        fields.append(SlackField(title="Result", value=truncate_text(result), short=False))

    attachment = SlackAttachment(
        fallback=f"Tool {tool_name} {status}",
        color=color,
        fields=fields,
        footer="Windows-Use Agent",
    )

    return SlackMessage(text=text, attachments=[attachment])


def format_agent_complete(
    is_success: bool, answer: str | None, error: str | None, steps: int, max_steps: int
) -> SlackMessage:
    """Format agent completion notification."""
    if is_success:
        text = f"{EMOJI_SUCCESS} *Agent Completed Successfully*"
        color = COLOR_SUCCESS
    else:
        text = f"{EMOJI_ERROR} *Agent Failed*"
        color = COLOR_ERROR

    fields = [
        SlackField(title="Status", value="Success" if is_success else "Failed", short=True),
        SlackField(title="Steps Used", value=f"{steps}/{max_steps}", short=True),
    ]

    if answer:
        fields.append(SlackField(title="Answer", value=truncate_text(answer), short=False))

    if error:
        fields.append(SlackField(title="Error", value=truncate_text(error), short=False))

    attachment = SlackAttachment(
        fallback=f"Agent {'completed' if is_success else 'failed'}",
        color=color,
        fields=fields,
        footer="Windows-Use Agent",
        ts=int(datetime.now().timestamp()),
    )

    return SlackMessage(text=text, attachments=[attachment])


def format_ui_event_focus(app_name: str, element_name: str) -> SlackMessage:
    """Format UI focus change event."""
    text = f"{EMOJI_FOCUS} Focus Changed"

    attachment = SlackAttachment(
        fallback=f"Focus changed to {element_name} in {app_name}",
        color=COLOR_INFO,
        fields=[
            SlackField(title="Application", value=app_name, short=True),
            SlackField(title="Element", value=element_name, short=True),
        ],
        footer="UI Event Monitor",
    )

    return SlackMessage(text=text, attachments=[attachment])


def format_ui_event_structure(event_type: str, app_name: str) -> SlackMessage:
    """Format UI structure change event."""
    text = f"{EMOJI_STRUCTURE} Structure Changed: {event_type}"

    attachment = SlackAttachment(
        fallback=f"UI structure changed in {app_name}",
        color=COLOR_WARNING,
        fields=[
            SlackField(title="Event Type", value=event_type, short=True),
            SlackField(title="Application", value=app_name, short=True),
        ],
        footer="UI Event Monitor",
    )

    return SlackMessage(text=text, attachments=[attachment])


def format_ui_event_property(property_name: str, app_name: str) -> SlackMessage:
    """Format UI property change event."""
    text = f"{EMOJI_PROPERTY} Property Changed: {property_name}"

    attachment = SlackAttachment(
        fallback=f"Property {property_name} changed in {app_name}",
        color=COLOR_INFO,
        fields=[
            SlackField(title="Property", value=property_name, short=True),
            SlackField(title="Application", value=app_name, short=True),
        ],
        footer="UI Event Monitor",
    )

    return SlackMessage(text=text, attachments=[attachment])


def format_error(error_message: str, context: str | None = None) -> SlackMessage:
    """Format error notification."""
    text = f"{EMOJI_ERROR} *Error Occurred*"

    fields = [SlackField(title="Error", value=truncate_text(error_message), short=False)]

    if context:
        fields.append(SlackField(title="Context", value=truncate_text(context), short=False))

    attachment = SlackAttachment(
        fallback=f"Error: {error_message}",
        color=COLOR_ERROR,
        fields=fields,
        footer="Windows-Use Agent",
        ts=int(datetime.now().timestamp()),
    )

    return SlackMessage(text=text, attachments=[attachment])


def format_custom_message(
    text: str, title: str | None = None, fields: dict[str, str] | None = None, color: str = COLOR_INFO
) -> SlackMessage:
    """Format a custom message with optional fields."""
    if not fields:
        # Simple text message
        return SlackMessage(text=text)

    # Message with attachment
    slack_fields = [
        SlackField(title=k, value=truncate_text(v), short=len(v) < 50) for k, v in fields.items()
    ]

    attachment = SlackAttachment(
        fallback=text,
        color=color,
        title=title,
        fields=slack_fields,
        footer="Windows-Use Agent",
    )

    return SlackMessage(text=text, attachments=[attachment])
