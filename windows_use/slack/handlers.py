"""Event handlers for Slack integration."""

import threading
import traceback
from typing import Any

from slack_bolt import App, Say, Ack

from windows_use.agent import Agent


class MessageHandler:
    """Handles Slack message events."""

    def __init__(self, agent: Agent, app: App, lock: threading.Lock):
        """
        Initialize message handler.

        Args:
            agent: Windows-Use agent instance
            app: Slack app instance
            lock: Thread lock for agent execution
        """
        self.agent = agent
        self.app = app
        self.lock = lock

    def handle_mention(self, event: dict[str, Any], say: Say) -> None:
        """
        Handle app mentions.

        Args:
            event: Slack event data
            say: Function to send messages
        """
        text = event.get("text", "")
        user = event.get("user", "unknown")

        # Remove bot mention from text
        bot_id = self.app.client.auth_test()["user_id"]
        text = text.replace(f"<@{bot_id}>", "").strip()

        if not text:
            say("👋 Hi! Please provide a task for me to execute on Windows.")
            return

        self._execute_task(text, say, user)

    def handle_message(self, event: dict[str, Any], say: Say) -> None:
        """
        Handle direct messages.

        Args:
            event: Slack event data
            say: Function to send messages
        """
        # Ignore bot messages and non-DM messages
        if event.get("bot_id") or event.get("channel_type") != "im":
            return

        text = event.get("text", "").strip()
        user = event.get("user", "unknown")

        if not text:
            return

        self._execute_task(text, say, user)

    def _execute_task(self, task: str, say: Say, user: str) -> None:
        """
        Execute a task using the agent.

        Args:
            task: Task description from user
            say: Function to send messages
            user: User ID who sent the message
        """
        # Send acknowledgment
        say(f"🤖 Executing task: `{task}`\n⏳ Please wait...")

        try:
            # Execute with thread lock to prevent concurrent executions
            with self.lock:
                result = self.agent.invoke(task)

                # Format and send response
                if result and hasattr(result, 'content'):
                    response = f"✅ Task completed!\n\n```\n{result.content}\n```"
                else:
                    response = "✅ Task completed!"

                say(response)

        except Exception as e:
            error_msg = f"❌ Error executing task:\n```\n{str(e)}\n```"
            say(error_msg)

            # Log full traceback for debugging
            print(f"Error executing task for user {user}:")
            traceback.print_exc()


class CommandHandler:
    """Handles Slack slash commands."""

    def __init__(self, agent: Agent, app: App, lock: threading.Lock):
        """
        Initialize command handler.

        Args:
            agent: Windows-Use agent instance
            app: Slack app instance
            lock: Thread lock for agent execution
        """
        self.agent = agent
        self.app = app
        self.lock = lock

    def handle_windows_command(self, ack: Ack, command: dict[str, Any], say: Say) -> None:
        """
        Handle /windows slash command.

        Args:
            ack: Acknowledge function
            command: Command data
            say: Function to send messages
        """
        ack()

        text = command.get("text", "").strip()
        user = command.get("user_id", "unknown")

        if not text:
            say("Usage: `/windows <task description>`\nExample: `/windows open notepad and type hello world`")
            return

        # Send acknowledgment
        say(f"🤖 Executing task: `{text}`\n⏳ Please wait...")

        try:
            # Execute with thread lock
            with self.lock:
                result = self.agent.invoke(text)

                # Format and send response
                if result and hasattr(result, 'content'):
                    response = f"✅ Task completed!\n\n```\n{result.content}\n```"
                else:
                    response = "✅ Task completed!"

                say(response)

        except Exception as e:
            error_msg = f"❌ Error executing task:\n```\n{str(e)}\n```"
            say(error_msg)

            # Log full traceback
            print(f"Error executing /windows command for user {user}:")
            traceback.print_exc()

    def handle_help_command(self, ack: Ack, say: Say) -> None:
        """
        Handle /windows-help slash command.

        Args:
            ack: Acknowledge function
            say: Function to send messages
        """
        ack()

        help_text = """
🤖 *Windows-Use Agent Help*

*Available Commands:*
• `/windows <task>` - Execute a Windows automation task
• `/windows-help` - Show this help message
• `/windows-status` - Check agent status

*How to use:*
1. Direct Message: Send me a DM with your task
2. Mention: @mention me in a channel with your task
3. Slash Command: Use `/windows <your task>`

*Example tasks:*
• `open notepad and type hello world`
• `take a screenshot and save it`
• `search for python tutorial in browser`
• `launch calculator and compute 5 + 7`

*Available Tools:*
The agent can click, type, scroll, launch apps, execute shell commands, and more!

For more info, visit: https://github.com/CursorTouch/Windows-Use
        """

        say(help_text)

    def handle_status_command(self, ack: Ack, say: Say) -> None:
        """
        Handle /windows-status slash command.

        Args:
            ack: Acknowledge function
            say: Function to send messages
        """
        ack()

        # Check if agent is busy
        is_busy = self.lock.locked()

        status_text = f"""
🤖 *Windows-Use Agent Status*

• Status: {"🔴 Busy" if is_busy else "🟢 Ready"}
• Version: 0.6.9
• Platform: Windows
• LLM: {self.agent.llm.__class__.__name__ if hasattr(self.agent, 'llm') else 'Unknown'}

{"The agent is currently executing a task. Please wait..." if is_busy else "Ready to accept new tasks!"}
        """

        say(status_text)
