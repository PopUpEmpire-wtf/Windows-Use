"""
Slack integration data models.

This module contains Pydantic models for Slack messages and events.
"""

from pydantic import BaseModel, Field
from typing import Any


class SlackField(BaseModel):
    """Represents a field in a Slack message attachment."""

    title: str
    value: str
    short: bool = False


class SlackAttachment(BaseModel):
    """Represents a Slack message attachment."""

    fallback: str
    color: str | None = None
    pretext: str | None = None
    author_name: str | None = None
    author_link: str | None = None
    author_icon: str | None = None
    title: str | None = None
    title_link: str | None = None
    text: str | None = None
    fields: list[SlackField] = Field(default_factory=list)
    footer: str | None = None
    footer_icon: str | None = None
    ts: int | None = None


class SlackBlock(BaseModel):
    """Represents a Slack Block Kit block."""

    type: str
    text: dict[str, str] | None = None
    elements: list[dict[str, Any]] | None = None
    accessory: dict[str, Any] | None = None
    fields: list[dict[str, str]] | None = None


class SlackMessage(BaseModel):
    """Represents a complete Slack message."""

    text: str
    channel: str | None = None
    username: str | None = None
    icon_emoji: str | None = None
    icon_url: str | None = None
    attachments: list[SlackAttachment] = Field(default_factory=list)
    blocks: list[SlackBlock] = Field(default_factory=list)


class SlackNotificationConfig(BaseModel):
    """Configuration for Slack notifications."""

    enabled: bool = True
    webhook_url: str | None = None
    bot_token: str | None = None
    channel: str | None = None
    username: str | None = None
    icon_emoji: str | None = None
    notify_agent_start: bool = True
    notify_agent_complete: bool = True
    notify_tool_execution: bool = True
    notify_ui_events: bool = False
    notify_errors: bool = True
