"""Main Slack service for Windows-Use agent."""

import os
import threading
from typing import Any, Optional

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from windows_use.agent import Agent
from windows_use.llms.base import LLMInterface
from windows_use.slack.handlers import MessageHandler, CommandHandler


class SlackAgent:
    """Slack integration service that routes Slack messages to Windows-Use agent."""

    def __init__(
        self,
        llm: LLMInterface,
        slack_bot_token: Optional[str] = None,
        slack_app_token: Optional[str] = None,
        **agent_config: Any
    ):
        """
        Initialize Slack agent.

        Args:
            llm: LLM interface for the agent
            slack_bot_token: Slack bot token (xoxb-...). If None, reads from SLACK_BOT_TOKEN env var
            slack_app_token: Slack app token (xapp-...). If None, reads from SLACK_APP_TOKEN env var
            **agent_config: Additional configuration passed to Agent
        """
        self.slack_bot_token = slack_bot_token or os.getenv("SLACK_BOT_TOKEN")
        self.slack_app_token = slack_app_token or os.getenv("SLACK_APP_TOKEN")

        if not self.slack_bot_token:
            raise ValueError(
                "SLACK_BOT_TOKEN is required. Set it via environment variable or constructor."
            )
        if not self.slack_app_token:
            raise ValueError(
                "SLACK_APP_TOKEN is required. Set it via environment variable or constructor."
            )

        # Initialize Slack app
        self.app = App(token=self.slack_bot_token)

        # Initialize Windows-Use agent
        self.agent = Agent(llm=llm, **agent_config)

        # Thread safety lock for agent execution
        self._agent_lock = threading.Lock()

        # Initialize handlers
        self.message_handler = MessageHandler(self.agent, self.app, self._agent_lock)
        self.command_handler = CommandHandler(self.agent, self.app, self._agent_lock)

        # Register event handlers
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register Slack event handlers."""
        # Handle direct messages and mentions
        self.app.event("app_mention")(self.message_handler.handle_mention)
        self.app.event("message")(self.message_handler.handle_message)

        # Handle slash commands
        self.app.command("/windows")(self.command_handler.handle_windows_command)
        self.app.command("/windows-help")(self.command_handler.handle_help_command)
        self.app.command("/windows-status")(self.command_handler.handle_status_command)

    def start(self, port: int = 3000) -> None:
        """
        Start the Slack agent using Socket Mode.

        Args:
            port: Port for the Socket Mode handler (default: 3000)
        """
        handler = SocketModeHandler(self.app, self.slack_app_token)
        print(f"⚡️ Windows-Use Slack agent is running on port {port}")
        handler.start()

    def stop(self) -> None:
        """Stop the Slack agent."""
        # Clean up resources if needed
        pass
