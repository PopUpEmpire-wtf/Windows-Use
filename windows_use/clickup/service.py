"""Main ClickUp service for Windows-Use agent."""

import os
import threading
from typing import Any

import uvicorn
from fastapi import FastAPI

from windows_use.agent import Agent
from windows_use.clickup.handlers import ClickUpClient, WebhookHandler
from windows_use.llms.base import BaseChatLLM


class ClickUpAgent:
    """ClickUp integration that routes ClickUp task events to the Windows-Use agent.

    The service exposes a ``POST /webhook`` endpoint that ClickUp calls for
    configured workspace events.  When a task tagged with ``task_tag`` is
    created, or when a comment that mentions ``bot_name`` is posted, the
    agent is invoked and the result is published back as a ClickUp comment.

    Example::

        from windows_use.clickup import ClickUpAgent
        from windows_use.llms.google import ChatGoogle

        llm = ChatGoogle(model="gemini-2.5-flash", api_key="...")
        clickup_agent = ClickUpAgent(llm=llm)
        clickup_agent.start()
    """

    def __init__(
        self,
        llm: BaseChatLLM,
        clickup_api_key: str | None = None,
        webhook_secret: str | None = None,
        task_tag: str = "windows-agent",
        bot_name: str = "windows-agent",
        **agent_config: Any,
    ):
        """
        Initialize the ClickUp agent.

        Args:
            llm: LLM instance conforming to ``BaseChatLLM``.
            clickup_api_key: ClickUp personal API token. Falls back to the
                ``CLICKUP_API_KEY`` environment variable.
            webhook_secret: Shared secret used to verify ClickUp webhook
                signatures. Falls back to ``CLICKUP_WEBHOOK_SECRET``.  When
                *None*, signature verification is skipped (not recommended for
                production).
            task_tag: Name of the ClickUp tag that marks tasks the agent
                should process when they are created (default:
                ``"windows-agent"``).
            bot_name: The mention name used to trigger the agent via task
                comments (default: ``"windows-agent"``). A comment starting
                with ``@windows-agent`` will be processed.
            **agent_config: Additional keyword arguments forwarded to
                :class:`~windows_use.agent.Agent` (e.g. ``browser``,
                ``use_vision``, ``max_steps``).

        Raises:
            ValueError: If ``clickup_api_key`` is not provided and the
                ``CLICKUP_API_KEY`` environment variable is not set.
        """
        self.clickup_api_key = clickup_api_key or os.getenv("CLICKUP_API_KEY")
        self.webhook_secret = webhook_secret or os.getenv("CLICKUP_WEBHOOK_SECRET")

        if not self.clickup_api_key:
            raise ValueError(
                "CLICKUP_API_KEY is required. "
                "Set it via the environment variable or the constructor argument."
            )

        # Initialize Windows-Use agent.
        self.agent = Agent(llm=llm, **agent_config)

        # Thread safety — prevent concurrent agent executions.
        self._agent_lock = threading.Lock()

        # ClickUp REST API client.
        self._clickup_client = ClickUpClient(self.clickup_api_key)

        # Webhook event handler.
        self._handler = WebhookHandler(
            agent=self.agent,
            lock=self._agent_lock,
            clickup_client=self._clickup_client,
            task_tag=task_tag,
            bot_name=bot_name,
        )

        # FastAPI application.
        self.app = FastAPI(title="Windows-Use ClickUp Agent")
        self._register_routes()

    def _register_routes(self) -> None:
        """Register HTTP routes on the FastAPI application."""
        from fastapi import Request

        @self.app.post("/webhook")
        async def webhook(request: Request) -> dict[str, str]:
            return await self._handler.handle_webhook(request, self.webhook_secret)

        @self.app.get("/health")
        async def health() -> dict[str, str | None]:
            return {
                "status": "ok",
                "agent": self.agent.__class__.__name__,
                "llm": self.agent.llm.__class__.__name__
                if hasattr(self.agent, "llm")
                else "unknown",
            }

    def start(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        """
        Start the webhook server using uvicorn.

        This call **blocks** until the server is stopped (e.g. via ``Ctrl+C``).

        Args:
            host: Network interface to bind to (default: ``"0.0.0.0"``).
            port: TCP port to listen on (default: ``8000``).
        """
        print(f"⚡️ Windows-Use ClickUp agent listening on http://{host}:{port}")
        uvicorn.run(self.app, host=host, port=port)
