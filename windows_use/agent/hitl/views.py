"""Data models for HITL approval system."""

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class ApprovalResult(str, Enum):
    """Approval decision outcomes."""

    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"


class ApprovalBackend(str, Enum):
    """Available approval backends."""

    CLI = "cli"
    SLACK = "slack"
    WEBHOOK = "webhook"
    AUTO_APPROVE = "auto_approve"  # For testing/bypass


class ApprovalRequest(BaseModel):
    """Request for human approval of a tool execution."""

    tool_name: str = Field(..., description="Name of the tool to execute")
    tool_description: str = Field(..., description="Description of what the tool does")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Tool execution parameters"
    )
    step_number: int = Field(..., description="Current agent step number")
    context: str = Field(default="", description="Additional context about the action")
    risk_level: str = Field(
        default="medium", description="Risk level: low, medium, high, critical"
    )


class ApprovalResponse(BaseModel):
    """Response from approval backend."""

    result: ApprovalResult = Field(..., description="Approval decision")
    message: str = Field(default="", description="Optional message from approver")
    approved_by: str = Field(default="", description="Identifier of who approved")
    timestamp: float = Field(default=0.0, description="Approval timestamp")
