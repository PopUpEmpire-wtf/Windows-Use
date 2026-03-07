"""Webhook event handlers and ClickUp REST API client for Windows-Use agent."""

import hashlib
import hmac
import logging
import re
import threading
from typing import Any

import httpx
from fastapi import HTTPException, Request

from windows_use.agent import Agent


logger = logging.getLogger(__name__)

_CLICKUP_API_BASE = "https://api.clickup.com/api/v2"


class ClickUpClient:
    """Thin client for the ClickUp REST API."""

    def __init__(self, api_key: str):
        """
        Initialize the ClickUp API client.

        Args:
            api_key: ClickUp personal API token or OAuth token.
        """
        self.api_key = api_key
        self._headers = {
            "Authorization": api_key,
            "Content-Type": "application/json",
        }

    def get_task(self, task_id: str) -> dict[str, Any]:
        """
        Fetch a task by its ID.

        Args:
            task_id: The ClickUp task ID.

        Returns:
            Task object as a dictionary.

        Raises:
            httpx.HTTPStatusError: If the request fails.
        """
        url = f"{_CLICKUP_API_BASE}/task/{task_id}"
        response = httpx.get(url, headers=self._headers, timeout=30)
        response.raise_for_status()
        return response.json()

    def get_comment(self, comment_id: str) -> dict[str, Any]:
        """
        Fetch a single comment by its ID.

        Args:
            comment_id: The ClickUp comment ID.

        Returns:
            Comment object as a dictionary.

        Raises:
            httpx.HTTPStatusError: If the request fails.
        """
        url = f"{_CLICKUP_API_BASE}/comment/{comment_id}"
        response = httpx.get(url, headers=self._headers, timeout=30)
        response.raise_for_status()
        return response.json()

    def post_comment(self, task_id: str, text: str) -> dict[str, Any]:
        """
        Post a comment on a ClickUp task.

        Args:
            task_id: The ClickUp task ID.
            text: Comment body.

        Returns:
            Created comment object as a dictionary.

        Raises:
            httpx.HTTPStatusError: If the request fails.
        """
        url = f"{_CLICKUP_API_BASE}/task/{task_id}/comment"
        payload = {"comment_text": text, "notify_all": False}
        response = httpx.post(url, headers=self._headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()


class WebhookHandler:
    """Handles incoming ClickUp webhook events."""

    def __init__(
        self,
        agent: Agent,
        lock: threading.Lock,
        clickup_client: ClickUpClient,
        task_tag: str,
        bot_name: str,
    ):
        """
        Initialize the webhook handler.

        Args:
            agent: Windows-Use agent instance.
            lock: Thread lock to prevent concurrent agent executions.
            clickup_client: ClickUp REST API client.
            task_tag: Tag name that marks tasks the agent should process.
            bot_name: Name prefix used to identify bot comments and trigger mentions.
        """
        self.agent = agent
        self.lock = lock
        self.client = clickup_client
        self.task_tag = task_tag
        self.bot_name = bot_name

    def _verify_signature(self, body: bytes, signature: str, secret: str) -> bool:
        """
        Verify the HMAC-SHA256 signature sent by ClickUp.

        Args:
            body: Raw request body bytes.
            signature: Value of the ``X-Signature`` request header.
            secret: Webhook secret configured in ClickUp.

        Returns:
            True if the signature is valid, False otherwise.
        """
        expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    async def handle_webhook(
        self, request: Request, webhook_secret: str | None
    ) -> dict[str, str]:
        """
        Entry point for all incoming ClickUp webhook POST requests.

        Args:
            request: The incoming FastAPI request.
            webhook_secret: Optional secret for request signature verification.

        Returns:
            Acknowledgement dict ``{"status": "ok"}``.
        """
        body = await request.body()

        # Verify request authenticity when a secret is configured.
        if webhook_secret:
            signature = request.headers.get("X-Signature", "")
            if not self._verify_signature(body, signature, webhook_secret):
                raise HTTPException(status_code=401, detail="Invalid webhook signature")

        payload: dict[str, Any] = await request.json()
        event: str = payload.get("event", "")
        task_id: str = payload.get("task_id", "")

        if event == "taskCreated" and task_id:
            threading.Thread(
                target=self._handle_task_created, args=(task_id,), daemon=True
            ).start()
        elif event == "taskCommentPosted" and task_id:
            history_items: list[dict] = payload.get("history_items", [])
            comment_id = self._extract_comment_id(history_items)
            if comment_id:
                threading.Thread(
                    target=self._handle_comment_posted,
                    args=(task_id, comment_id),
                    daemon=True,
                ).start()

        return {"status": "ok"}

    def _extract_comment_id(self, history_items: list[dict]) -> str | None:
        """Return the comment ID from a ``taskCommentPosted`` history_items list."""
        for item in history_items:
            comment = item.get("comment", {})
            if comment:
                return str(comment.get("id", ""))
        return None

    def _handle_task_created(self, task_id: str) -> None:
        """
        Process a newly created task.

        A task is dispatched to the agent only when it carries the configured
        ``task_tag``.  The agent result is posted back as a task comment.

        Args:
            task_id: ClickUp task ID.
        """
        try:
            task = self.client.get_task(task_id)
        except Exception as exc:
            logger.error("[ClickUp] Failed to fetch task %s: %s", task_id, exc)
            return

        # Check whether the task has the sentinel tag.
        tags: list[dict] = task.get("tags", [])
        tag_names = {t.get("name", "").lower() for t in tags}
        if self.task_tag.lower() not in tag_names:
            return

        task_name: str = task.get("name", "")
        task_description: str = task.get("description", "") or task_name

        self._run_agent(task_id, task_description or task_name)

    def _handle_comment_posted(self, task_id: str, comment_id: str) -> None:
        """
        Process a new comment posted on a task.

        The agent is triggered only when the comment starts with a mention of
        ``self.bot_name`` (e.g. ``@windows-agent``).

        Args:
            task_id: ClickUp task ID.
            comment_id: ClickUp comment ID.
        """
        try:
            comment_data = self.client.get_comment(comment_id)
        except Exception as exc:
            logger.error("[ClickUp] Failed to fetch comment %s: %s", comment_id, exc)
            return

        comment_text: str = comment_data.get("comment_text", "").strip()

        # Ignore comments that do not mention the bot.
        mention_pattern = rf"^@{re.escape(self.bot_name)}\s*"
        if not re.match(mention_pattern, comment_text, flags=re.IGNORECASE):
            return

        # Strip the mention prefix before passing to the agent.
        task_text = re.sub(
            mention_pattern, "", comment_text, flags=re.IGNORECASE
        ).strip()
        if not task_text:
            self.client.post_comment(
                task_id, "👋 Please provide a task description after the mention."
            )
            return

        self._run_agent(task_id, task_text)

    def _run_agent(self, task_id: str, task: str) -> None:
        """
        Execute a task via the Windows-Use agent and post the result as a comment.

        Args:
            task_id: ClickUp task ID used for posting the result comment.
            task: Natural language task description for the agent.
        """
        logger.info("[ClickUp] Executing task on task %s: %r", task_id, task)
        try:
            with self.lock:
                result = self.agent.invoke(task)

            if result and hasattr(result, "content") and result.content:
                comment = f"✅ Task completed!\n\n{result.content}"
            else:
                comment = "✅ Task completed!"

            self.client.post_comment(task_id, comment)

        except Exception as exc:
            error_comment = f"❌ Error executing task:\n\n```\n{exc}\n```"
            logger.exception("Error executing task on task %s", task_id)
            try:
                self.client.post_comment(task_id, error_comment)
            except Exception:
                pass
