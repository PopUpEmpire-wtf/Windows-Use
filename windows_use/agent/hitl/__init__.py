"""Human-In-The-Loop (HITL) approval system for Windows-Use agent."""

from windows_use.agent.hitl.service import HITLApprovalService
from windows_use.agent.hitl.views import (
    ApprovalRequest,
    ApprovalResponse,
    ApprovalBackend,
    ApprovalResult,
)

__all__ = [
    "HITLApprovalService",
    "ApprovalRequest",
    "ApprovalResponse",
    "ApprovalBackend",
    "ApprovalResult",
]
