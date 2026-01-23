"""Tests for HITL (Human-In-The-Loop) approval system."""

import pytest
from unittest.mock import MagicMock, patch
from windows_use.agent.hitl.service import (
    HITLApprovalService,
    CLIApprovalBackend,
    get_tool_risk_level,
)
from windows_use.agent.hitl.views import (
    ApprovalBackend,
    ApprovalRequest,
    ApprovalResponse,
    ApprovalResult,
)


class TestToolRiskClassification:
    """Test tool risk level classification."""

    def test_critical_risk_tools(self):
        """Test that shell_tool is classified as critical."""
        assert get_tool_risk_level("shell_tool") == "critical"

    def test_high_risk_tools(self):
        """Test that app_tool and memory_tool are high risk."""
        assert get_tool_risk_level("app_tool") == "high"
        assert get_tool_risk_level("memory_tool") == "high"

    def test_medium_risk_tools(self):
        """Test that click_tool, type_tool are medium risk."""
        assert get_tool_risk_level("click_tool") == "medium"
        assert get_tool_risk_level("type_tool") == "medium"

    def test_low_risk_tools(self):
        """Test that scroll_tool, wait_tool are low risk."""
        assert get_tool_risk_level("scroll_tool") == "low"
        assert get_tool_risk_level("wait_tool") == "low"

    def test_unknown_tool_defaults_to_low(self):
        """Test that unknown tools default to low risk."""
        assert get_tool_risk_level("unknown_tool") == "low"


class TestHITLApprovalService:
    """Test HITL approval service."""

    def test_auto_approve_backend(self):
        """Test that AUTO_APPROVE backend approves all requests."""
        service = HITLApprovalService(backend=ApprovalBackend.AUTO_APPROVE)

        response = service.request_approval(
            tool_name="shell_tool",
            tool_description="Execute shell command",
            parameters={"command": "dir"},
            step_number=1,
        )

        assert response.result == ApprovalResult.APPROVED
        assert response.approved_by == "system"

    def test_requires_approval_by_tool_name(self):
        """Test approval requirement by specific tool name."""
        service = HITLApprovalService(
            backend=ApprovalBackend.CLI,
            require_approval_for={"click_tool", "type_tool"},
        )

        assert service.requires_approval("click_tool", "medium") is True
        assert service.requires_approval("type_tool", "medium") is True
        assert service.requires_approval("scroll_tool", "low") is False

    def test_requires_approval_by_risk_level(self):
        """Test approval requirement by risk level."""
        # Only high and critical require approval
        service = HITLApprovalService(
            backend=ApprovalBackend.CLI, min_risk_level="high"
        )

        assert service.requires_approval("shell_tool", "critical") is True
        assert service.requires_approval("app_tool", "high") is True
        assert service.requires_approval("click_tool", "medium") is False
        assert service.requires_approval("scroll_tool", "low") is False

    def test_requires_approval_medium_risk_level(self):
        """Test approval requirement with medium risk threshold."""
        # Medium, high, and critical require approval
        service = HITLApprovalService(
            backend=ApprovalBackend.CLI, min_risk_level="medium"
        )

        assert service.requires_approval("shell_tool", "critical") is True
        assert service.requires_approval("app_tool", "high") is True
        assert service.requires_approval("click_tool", "medium") is True
        assert service.requires_approval("scroll_tool", "low") is False

    def test_auto_approve_low_risk_tools(self):
        """Test that low risk tools are auto-approved."""
        service = HITLApprovalService(
            backend=ApprovalBackend.CLI, min_risk_level="high"
        )

        response = service.request_approval(
            tool_name="scroll_tool",
            tool_description="Scroll the page",
            parameters={"direction": "down"},
            step_number=1,
        )

        assert response.result == ApprovalResult.APPROVED
        assert response.approved_by == "system"
        assert "Auto-approved" in response.message

    @patch.object(CLIApprovalBackend, "request_approval")
    def test_cli_approval_approved(self, mock_cli_approve):
        """Test CLI approval when user approves."""
        mock_cli_approve.return_value = ApprovalResponse(
            result=ApprovalResult.APPROVED,
            message="Approved via CLI",
            approved_by="human",
            timestamp=123.45,
        )

        service = HITLApprovalService(
            backend=ApprovalBackend.CLI, min_risk_level="high"
        )

        response = service.request_approval(
            tool_name="shell_tool",
            tool_description="Execute shell command",
            parameters={"command": "echo test"},
            step_number=1,
        )

        assert response.result == ApprovalResult.APPROVED
        assert response.approved_by == "human"
        mock_cli_approve.assert_called_once()

    @patch.object(CLIApprovalBackend, "request_approval")
    def test_cli_approval_rejected(self, mock_cli_approve):
        """Test CLI approval when user rejects."""
        mock_cli_approve.return_value = ApprovalResponse(
            result=ApprovalResult.REJECTED,
            message="Rejected via CLI",
            approved_by="human",
            timestamp=123.45,
        )

        service = HITLApprovalService(
            backend=ApprovalBackend.CLI, min_risk_level="high"
        )

        response = service.request_approval(
            tool_name="shell_tool",
            tool_description="Execute shell command",
            parameters={"command": "rm -rf /"},
            step_number=1,
        )

        assert response.result == ApprovalResult.REJECTED
        assert response.approved_by == "human"

    def test_custom_approver(self):
        """Test custom approval function."""

        def custom_approver(request: ApprovalRequest) -> ApprovalResponse:
            # Auto-reject all shell commands
            if request.tool_name == "shell_tool":
                return ApprovalResponse(
                    result=ApprovalResult.REJECTED,
                    message="Shell commands not allowed",
                    approved_by="custom_policy",
                    timestamp=0.0,
                )
            return ApprovalResponse(
                result=ApprovalResult.APPROVED,
                message="Approved by custom policy",
                approved_by="custom_policy",
                timestamp=0.0,
            )

        service = HITLApprovalService(
            backend=ApprovalBackend.CLI,
            min_risk_level="low",
            custom_approver=custom_approver,
        )

        # Shell command should be rejected
        response = service.request_approval(
            tool_name="shell_tool",
            tool_description="Execute shell command",
            parameters={"command": "dir"},
            step_number=1,
        )
        assert response.result == ApprovalResult.REJECTED
        assert response.approved_by == "custom_policy"

        # Other tools should be approved
        response = service.request_approval(
            tool_name="click_tool",
            tool_description="Click element",
            parameters={"x": 100, "y": 200},
            step_number=2,
        )
        assert response.result == ApprovalResult.APPROVED
        assert response.approved_by == "custom_policy"

    def test_slack_backend_requires_webhook(self):
        """Test that Slack backend requires webhook URL."""
        with pytest.raises(ValueError, match="slack_webhook_url required"):
            HITLApprovalService(backend=ApprovalBackend.SLACK)

    def test_slack_backend_initialization(self):
        """Test Slack backend initialization with webhook."""
        service = HITLApprovalService(
            backend=ApprovalBackend.SLACK,
            slack_webhook_url="https://hooks.slack.com/test",
        )
        assert service.backend == ApprovalBackend.SLACK
        assert service.approver is not None


class TestApprovalRequest:
    """Test ApprovalRequest model."""

    def test_approval_request_creation(self):
        """Test creating an approval request."""
        request = ApprovalRequest(
            tool_name="click_tool",
            tool_description="Click at coordinates",
            parameters={"x": 100, "y": 200},
            step_number=5,
            context="Clicking button",
            risk_level="medium",
        )

        assert request.tool_name == "click_tool"
        assert request.parameters["x"] == 100
        assert request.step_number == 5
        assert request.risk_level == "medium"

    def test_approval_request_defaults(self):
        """Test approval request default values."""
        request = ApprovalRequest(
            tool_name="test_tool",
            tool_description="Test",
            step_number=1,
        )

        assert request.parameters == {}
        assert request.context == ""
        assert request.risk_level == "medium"


class TestApprovalResponse:
    """Test ApprovalResponse model."""

    def test_approval_response_creation(self):
        """Test creating an approval response."""
        response = ApprovalResponse(
            result=ApprovalResult.APPROVED,
            message="Approved",
            approved_by="human",
            timestamp=123.45,
        )

        assert response.result == ApprovalResult.APPROVED
        assert response.message == "Approved"
        assert response.approved_by == "human"
        assert response.timestamp == 123.45

    def test_approval_response_defaults(self):
        """Test approval response default values."""
        response = ApprovalResponse(result=ApprovalResult.REJECTED)

        assert response.message == ""
        assert response.approved_by == ""
        assert response.timestamp == 0.0
