"""
Slack integration service.

This module provides the SlackIntegration class for sending notifications
to Slack channels via webhooks or Bot API.
"""

import logging
import os
import time
from typing import Any

from dotenv import load_dotenv

from windows_use.slack.views import SlackMessage, SlackNotificationConfig
from windows_use.slack.config import (
    DEFAULT_CHANNEL,
    DEFAULT_USERNAME,
    DEFAULT_ICON_EMOJI,
    ENV_SLACK_WEBHOOK_URL,
    ENV_SLACK_BOT_TOKEN,
    ENV_SLACK_CHANNEL,
    ENV_SLACK_ENABLED,
    MIN_NOTIFICATION_INTERVAL,
)

load_dotenv()

logger = logging.getLogger(__name__)


class SlackIntegration:
    """
    Slack integration for Windows-Use agent.

    Supports both webhook and Bot API methods for sending notifications.
    Handles rate limiting and error handling.
    """

    def __init__(self, config: SlackNotificationConfig | None = None):
        """
        Initialize Slack integration.

        Args:
            config: Optional configuration. If None, reads from environment variables.
        """
        self.config = config or self._load_config_from_env()
        self.webhook_client = None
        self.bot_client = None
        self.last_notification_time = 0

        # Initialize clients based on configuration
        if self.config.enabled:
            self._initialize_clients()

    def _load_config_from_env(self) -> SlackNotificationConfig:
        """Load configuration from environment variables."""
        enabled = os.getenv(ENV_SLACK_ENABLED, "false").lower() in ("true", "1", "yes")

        return SlackNotificationConfig(
            enabled=enabled,
            webhook_url=os.getenv(ENV_SLACK_WEBHOOK_URL),
            bot_token=os.getenv(ENV_SLACK_BOT_TOKEN),
            channel=os.getenv(ENV_SLACK_CHANNEL, DEFAULT_CHANNEL),
            username=DEFAULT_USERNAME,
            icon_emoji=DEFAULT_ICON_EMOJI,
        )

    def _initialize_clients(self):
        """Initialize Slack clients based on available credentials."""
        # Initialize webhook client if URL is provided
        if self.config.webhook_url:
            try:
                from slack_sdk.webhook import WebhookClient

                self.webhook_client = WebhookClient(self.config.webhook_url)
                logger.info("[Slack] Webhook client initialized")
            except ImportError:
                logger.error(
                    "[Slack] slack-sdk not installed. Run: pip install slack-sdk"
                )
            except Exception as e:
                logger.error(f"[Slack] Failed to initialize webhook client: {e}")

        # Initialize Bot API client if token is provided
        if self.config.bot_token:
            try:
                from slack_sdk import WebClient

                self.bot_client = WebClient(token=self.config.bot_token)
                logger.info("[Slack] Bot client initialized")
            except ImportError:
                logger.error(
                    "[Slack] slack-sdk not installed. Run: pip install slack-sdk"
                )
            except Exception as e:
                logger.error(f"[Slack] Failed to initialize bot client: {e}")

        if not self.webhook_client and not self.bot_client:
            logger.warning(
                "[Slack] No Slack credentials provided. Set SLACK_WEBHOOK_URL or SLACK_BOT_TOKEN"
            )
            self.config.enabled = False

    def _rate_limit_check(self) -> bool:
        """
        Check if enough time has passed since last notification.

        Returns:
            True if notification can be sent, False otherwise
        """
        current_time = time.time()
        time_since_last = current_time - self.last_notification_time

        if time_since_last < MIN_NOTIFICATION_INTERVAL:
            logger.debug(
                f"[Slack] Rate limit: {MIN_NOTIFICATION_INTERVAL - time_since_last:.2f}s remaining"
            )
            return False

        self.last_notification_time = current_time
        return True

    def _convert_message_to_webhook_payload(self, message: SlackMessage) -> dict[str, Any]:
        """Convert SlackMessage to webhook payload format."""
        payload = {"text": message.text}

        if message.username or self.config.username:
            payload["username"] = message.username or self.config.username

        if message.icon_emoji or self.config.icon_emoji:
            payload["icon_emoji"] = message.icon_emoji or self.config.icon_emoji

        if message.channel or self.config.channel:
            payload["channel"] = message.channel or self.config.channel

        if message.attachments:
            payload["attachments"] = [att.model_dump(exclude_none=True) for att in message.attachments]

        if message.blocks:
            payload["blocks"] = [block.model_dump(exclude_none=True) for block in message.blocks]

        return payload

    def _convert_message_to_bot_payload(self, message: SlackMessage) -> dict[str, Any]:
        """Convert SlackMessage to Bot API payload format."""
        payload = {
            "text": message.text,
            "channel": message.channel or self.config.channel or DEFAULT_CHANNEL,
        }

        if message.username or self.config.username:
            payload["username"] = message.username or self.config.username

        if message.icon_emoji or self.config.icon_emoji:
            payload["icon_emoji"] = message.icon_emoji or self.config.icon_emoji

        if message.attachments:
            payload["attachments"] = [att.model_dump(exclude_none=True) for att in message.attachments]

        if message.blocks:
            payload["blocks"] = [block.model_dump(exclude_none=True) for block in message.blocks]

        return payload

    def send(self, message: SlackMessage, bypass_rate_limit: bool = False) -> bool:
        """
        Send a message to Slack.

        Args:
            message: The SlackMessage to send
            bypass_rate_limit: If True, skip rate limiting

        Returns:
            True if message sent successfully, False otherwise
        """
        if not self.config.enabled:
            logger.debug("[Slack] Notifications disabled, skipping message")
            return False

        # Rate limiting
        if not bypass_rate_limit and not self._rate_limit_check():
            return False

        # Try webhook first, then Bot API
        if self.webhook_client:
            return self._send_via_webhook(message)
        elif self.bot_client:
            return self._send_via_bot(message)
        else:
            logger.warning("[Slack] No Slack client available")
            return False

    def _send_via_webhook(self, message: SlackMessage) -> bool:
        """Send message via webhook."""
        try:
            payload = self._convert_message_to_webhook_payload(message)
            response = self.webhook_client.send(**payload)

            if response.status_code == 200:
                logger.debug("[Slack] Message sent via webhook")
                return True
            else:
                logger.error(f"[Slack] Webhook failed: {response.status_code} - {response.body}")
                return False

        except Exception as e:
            logger.error(f"[Slack] Webhook error: {e}")
            return False

    def _send_via_bot(self, message: SlackMessage) -> bool:
        """Send message via Bot API."""
        try:
            payload = self._convert_message_to_bot_payload(message)
            response = self.bot_client.chat_postMessage(**payload)

            if response["ok"]:
                logger.debug("[Slack] Message sent via Bot API")
                return True
            else:
                logger.error(f"[Slack] Bot API failed: {response.get('error', 'Unknown error')}")
                return False

        except Exception as e:
            logger.error(f"[Slack] Bot API error: {e}")
            return False

    def send_text(self, text: str, channel: str | None = None) -> bool:
        """
        Send a simple text message.

        Args:
            text: The message text
            channel: Optional channel override

        Returns:
            True if message sent successfully, False otherwise
        """
        message = SlackMessage(text=text, channel=channel)
        return self.send(message)

    def is_enabled(self) -> bool:
        """Check if Slack integration is enabled and configured."""
        return self.config.enabled and (self.webhook_client is not None or self.bot_client is not None)
