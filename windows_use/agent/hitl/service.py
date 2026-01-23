"""HITL approval service implementation."""

import logging
import time
from typing import Callable, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from windows_use.agent.hitl.views import (
    ApprovalBackend,
    ApprovalRequest,
    ApprovalResponse,
    ApprovalResult,
)

logger = logging.getLogger(__name__)
console = Console()


# Tool risk classifications
CRITICAL_RISK_TOOLS = {
    "shell_tool",  # Can execute any command
}

HIGH_RISK_TOOLS = {
    "app_tool",  # Can launch/close applications
    "memory_tool",  # Can modify persistent storage
}

MEDIUM_RISK_TOOLS = {
    "type_tool",  # Can input text
    "click_tool",  # Can click UI elements
    "drag_tool",  # Can drag elements
    "shortcut_tool",  # Can trigger shortcuts
    "multi_edit_tool",  # Can edit multiple fields
}

LOW_RISK_TOOLS = {
    "scroll_tool",  # Just scrolling
    "move_tool",  # Just mouse movement
    "wait_tool",  # Just waiting
    "scrape_tool",  # Read-only
    "done_tool",  # Signals completion
}


def get_tool_risk_level(tool_name: str) -> str:
    """Determine risk level for a tool.

    Args:
        tool_name: Name of the tool

    Returns:
        Risk level: critical, high, medium, or low
    """
    if tool_name in CRITICAL_RISK_TOOLS:
        return "critical"
    elif tool_name in HIGH_RISK_TOOLS:
        return "high"
    elif tool_name in MEDIUM_RISK_TOOLS:
        return "medium"
    else:
        return "low"


class CLIApprovalBackend:
    """CLI-based approval backend using interactive prompts."""

    def __init__(self, timeout: int = 60):
        """Initialize CLI approval backend.

        Args:
            timeout: Seconds to wait for approval (default: 60)
        """
        self.timeout = timeout

    def request_approval(self, request: ApprovalRequest) -> ApprovalResponse:
        """Request approval via CLI prompt.

        Args:
            request: Approval request details

        Returns:
            Approval response with decision
        """
        # Display approval request
        risk_colors = {
            "critical": "red bold",
            "high": "red",
            "medium": "yellow",
            "low": "green",
        }
        risk_color = risk_colors.get(request.risk_level, "white")

        panel_content = f"""
[bold]Tool:[/bold] {request.tool_name}
[bold]Description:[/bold] {request.tool_description}
[bold]Risk Level:[/bold] [{risk_color}]{request.risk_level.upper()}[/{risk_color}]
[bold]Step:[/bold] {request.step_number}

[bold]Parameters:[/bold]
"""
        for key, value in request.parameters.items():
            # Truncate long values
            value_str = str(value)
            if len(value_str) > 100:
                value_str = value_str[:100] + "..."
            panel_content += f"  • {key}: {value_str}\n"

        if request.context:
            panel_content += f"\n[bold]Context:[/bold] {request.context}"

        console.print(
            Panel(
                panel_content.strip(),
                title="[bold cyan]🔐 HITL Approval Required[/bold cyan]",
                border_style="cyan",
            )
        )

        # Prompt for approval
        try:
            choice = Prompt.ask(
                "\n[bold]Approve this action?[/bold]",
                choices=["y", "n", "d"],
                default="y",
                show_choices=True,
                console=console,
            )

            if choice.lower() == "y":
                return ApprovalResponse(
                    result=ApprovalResult.APPROVED,
                    message="Approved via CLI",
                    approved_by="human",
                    timestamp=time.time(),
                )
            elif choice.lower() == "d":
                # Show detailed parameters
                console.print("\n[bold]Full Parameters:[/bold]")
                console.print(request.parameters)
                # Ask again
                return self.request_approval(request)
            else:
                return ApprovalResponse(
                    result=ApprovalResult.REJECTED,
                    message="Rejected via CLI",
                    approved_by="human",
                    timestamp=time.time(),
                )

        except (KeyboardInterrupt, EOFError):
            logger.warning("Approval interrupted by user")
            return ApprovalResponse(
                result=ApprovalResult.REJECTED,
                message="Interrupted by user",
                approved_by="human",
                timestamp=time.time(),
            )


class SlackApprovalBackend:
    """Slack-based approval backend using webhooks and interactive messages."""

    def __init__(
        self, webhook_url: str, slack_token: Optional[str] = None, timeout: int = 300
    ):
        """Initialize Slack approval backend.

        Args:
            webhook_url: Slack webhook URL for notifications
            slack_token: Slack bot token for interactive messages (optional)
            timeout: Seconds to wait for approval (default: 300)
        """
        self.webhook_url = webhook_url
        self.slack_token = slack_token
        self.timeout = timeout

    def request_approval(self, request: ApprovalRequest) -> ApprovalResponse:
        """Request approval via Slack message.

        Args:
            request: Approval request details

        Returns:
            Approval response with decision
        """
        try:
            import requests
        except ImportError:
            logger.error("requests library required for Slack integration")
            return ApprovalResponse(
                result=ApprovalResult.REJECTED,
                message="Slack integration not available",
                approved_by="system",
                timestamp=time.time(),
            )

        # Build Slack message
        risk_emojis = {
            "critical": ":red_circle:",
            "high": ":orange_circle:",
            "medium": ":yellow_circle:",
            "low": ":green_circle:",
        }
        risk_emoji = risk_emojis.get(request.risk_level, ":white_circle:")

        params_text = "\n".join(
            [f"• *{k}*: `{v}`" for k, v in request.parameters.items()]
        )

        slack_message = {
            "text": f"{risk_emoji} *HITL Approval Required* - Step {request.step_number}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🔐 Approval Required - Step {request.step_number}",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Tool:*\n{request.tool_name}"},
                        {
                            "type": "mrkdwn",
                            "text": f"*Risk:*\n{risk_emoji} {request.risk_level.upper()}",
                        },
                    ],
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Description:*\n{request.tool_description}",
                    },
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Parameters:*\n{params_text}"},
                },
            ],
        }

        if request.context:
            slack_message["blocks"].append(
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Context:*\n{request.context}"},
                }
            )

        # Add action buttons if we have a Slack token
        if self.slack_token:
            slack_message["blocks"].append(
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "✅ Approve"},
                            "style": "primary",
                            "value": "approve",
                            "action_id": "approve_action",
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "❌ Reject"},
                            "style": "danger",
                            "value": "reject",
                            "action_id": "reject_action",
                        },
                    ],
                }
            )

        # Send to Slack
        try:
            response = requests.post(self.webhook_url, json=slack_message, timeout=10)
            response.raise_for_status()
            logger.info("Approval request sent to Slack")

            # If we have interactive buttons, wait for response
            # For now, this is a simplified implementation - in production,
            # you'd need a Flask/FastAPI server to receive Slack callbacks
            if self.slack_token:
                console.print(
                    "[yellow]Waiting for Slack approval (check your Slack workspace)...[/yellow]"
                )
                # TODO: Implement proper callback handling
                # For now, fall back to CLI
                logger.warning(
                    "Interactive Slack approval not yet implemented, falling back to CLI"
                )
                return CLIApprovalBackend().request_approval(request)
            else:
                # No interactive buttons, fall back to CLI
                console.print("[yellow]Slack notification sent, approve via CLI:[/yellow]")
                return CLIApprovalBackend().request_approval(request)

        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")
            # Fall back to CLI
            return CLIApprovalBackend().request_approval(request)


class HITLApprovalService:
    """Service for managing human-in-the-loop approvals."""

    def __init__(
        self,
        backend: ApprovalBackend = ApprovalBackend.CLI,
        require_approval_for: Optional[set[str]] = None,
        min_risk_level: str = "high",
        slack_webhook_url: Optional[str] = None,
        slack_token: Optional[str] = None,
        custom_approver: Optional[Callable[[ApprovalRequest], ApprovalResponse]] = None,
    ):
        """Initialize HITL approval service.

        Args:
            backend: Approval backend to use
            require_approval_for: Set of tool names requiring approval (None = use risk level)
            min_risk_level: Minimum risk level requiring approval (critical, high, medium, low)
            slack_webhook_url: Slack webhook URL (for Slack backend)
            slack_token: Slack bot token (for interactive Slack messages)
            custom_approver: Custom approval function
        """
        self.backend = backend
        self.require_approval_for = require_approval_for
        self.min_risk_level = min_risk_level
        self.custom_approver = custom_approver

        # Initialize backend
        if backend == ApprovalBackend.CLI:
            self.approver = CLIApprovalBackend()
        elif backend == ApprovalBackend.SLACK:
            if not slack_webhook_url:
                raise ValueError("slack_webhook_url required for Slack backend")
            self.approver = SlackApprovalBackend(slack_webhook_url, slack_token)
        elif backend == ApprovalBackend.AUTO_APPROVE:
            self.approver = None  # Auto-approve everything
        else:
            self.approver = CLIApprovalBackend()  # Default to CLI

        logger.info(f"HITL approval service initialized with backend: {backend}")

    def requires_approval(self, tool_name: str, risk_level: str) -> bool:
        """Check if a tool requires approval.

        Args:
            tool_name: Name of the tool
            risk_level: Risk level of the tool

        Returns:
            True if approval is required
        """
        # If specific tools are configured, check those
        if self.require_approval_for is not None:
            return tool_name in self.require_approval_for

        # Otherwise, use risk level
        risk_hierarchy = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        min_level = risk_hierarchy.get(self.min_risk_level, 3)
        tool_level = risk_hierarchy.get(risk_level, 2)

        return tool_level >= min_level

    def request_approval(
        self,
        tool_name: str,
        tool_description: str,
        parameters: dict,
        step_number: int,
        context: str = "",
    ) -> ApprovalResponse:
        """Request approval for a tool execution.

        Args:
            tool_name: Name of the tool
            tool_description: Description of what the tool does
            parameters: Tool parameters
            step_number: Current agent step number
            context: Additional context

        Returns:
            Approval response
        """
        # Auto-approve if backend is AUTO_APPROVE
        if self.backend == ApprovalBackend.AUTO_APPROVE:
            return ApprovalResponse(
                result=ApprovalResult.APPROVED,
                message="Auto-approved",
                approved_by="system",
                timestamp=time.time(),
            )

        # Determine risk level
        risk_level = get_tool_risk_level(tool_name)

        # Check if approval is required
        if not self.requires_approval(tool_name, risk_level):
            logger.debug(f"Tool {tool_name} does not require approval")
            return ApprovalResponse(
                result=ApprovalResult.APPROVED,
                message="Auto-approved (low risk)",
                approved_by="system",
                timestamp=time.time(),
            )

        # Build approval request
        request = ApprovalRequest(
            tool_name=tool_name,
            tool_description=tool_description,
            parameters=parameters,
            step_number=step_number,
            context=context,
            risk_level=risk_level,
        )

        # Use custom approver if provided
        if self.custom_approver:
            try:
                return self.custom_approver(request)
            except Exception as e:
                logger.error(f"Custom approver failed: {e}, falling back to default")

        # Request approval via backend
        logger.info(f"Requesting approval for {tool_name} (risk: {risk_level})")
        response = self.approver.request_approval(request)

        logger.info(
            f"Approval decision: {response.result} by {response.approved_by}"
        )
        return response
