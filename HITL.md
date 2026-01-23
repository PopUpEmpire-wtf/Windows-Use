# Human-In-The-Loop (HITL) Approval System

## Overview

The Human-In-The-Loop (HITL) system provides an approval mechanism for Windows-Use agent tool executions. It allows you to review and approve/reject actions before they are performed, adding an essential layer of control and safety for automated Windows operations.

## Why Use HITL?

Windows-Use operates directly on your Windows system without sandboxing. HITL helps by:

- **Preventing unintended actions**: Review each operation before execution
- **Security auditing**: Log and track all approved/rejected actions
- **Risk management**: Auto-approve low-risk operations, review high-risk ones
- **Compliance**: Meet organizational requirements for human oversight
- **Learning mode**: Understand what the agent is doing step-by-step

## Quick Start

### Basic Usage

```python
from windows_use.agent import Agent, Browser
from windows_use.agent.hitl.views import ApprovalBackend
from windows_use.llms.anthropic import ChatAnthropic

llm = ChatAnthropic(model="claude-sonnet-4-5", api_key="your-api-key")

# Enable HITL with CLI approval
agent = Agent(
    llm=llm,
    enable_hitl=True,
    hitl_backend=ApprovalBackend.CLI,
    hitl_min_risk_level="high"  # Only high/critical risk tools need approval
)

agent.print_response("Open notepad")
```

When the agent attempts to execute a high-risk tool, you'll see a prompt:

```
┌──────────────────────────────────────────────────────────┐
│             🔐 HITL Approval Required                    │
├──────────────────────────────────────────────────────────┤
│ Tool: app_tool                                           │
│ Description: Launch, switch, or resize applications      │
│ Risk Level: HIGH                                         │
│ Step: 1                                                  │
│                                                          │
│ Parameters:                                              │
│   • name: notepad                                        │
│   • status: launch                                       │
│                                                          │
│ Context: Agent requesting to execute app_tool            │
└──────────────────────────────────────────────────────────┘

Approve this action? [y/n/d] (y):
```

- **y**: Approve and execute
- **n**: Reject (agent will receive error)
- **d**: Show detailed parameters

## Configuration Options

### 1. Approval Backends

HITL supports multiple approval backends:

#### CLI (Command Line Interface)
Interactive terminal prompts for approval.

```python
agent = Agent(
    llm=llm,
    enable_hitl=True,
    hitl_backend=ApprovalBackend.CLI
)
```

#### Slack
Send approval requests to Slack workspace.

```python
agent = Agent(
    llm=llm,
    enable_hitl=True,
    hitl_backend=ApprovalBackend.SLACK,
    hitl_slack_webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
)
```

**Note**: Currently falls back to CLI for actual approval. Full Slack interactive buttons require additional setup.

#### Auto-Approve
Bypass approval (for testing/trusted environments).

```python
agent = Agent(
    llm=llm,
    enable_hitl=True,
    hitl_backend=ApprovalBackend.AUTO_APPROVE
)
```

### 2. Risk-Based Approval

Control which tools require approval based on risk level:

```python
# Only critical and high-risk tools
agent = Agent(
    llm=llm,
    enable_hitl=True,
    hitl_min_risk_level="high"
)

# Medium, high, and critical risk tools
agent = Agent(
    llm=llm,
    enable_hitl=True,
    hitl_min_risk_level="medium"
)

# All tools (maximum safety)
agent = Agent(
    llm=llm,
    enable_hitl=True,
    hitl_min_risk_level="low"
)
```

#### Tool Risk Levels

| Risk Level | Tools |
|------------|-------|
| **Critical** | `shell_tool` (can execute any command) |
| **High** | `app_tool` (launch/close apps), `memory_tool` (persistent storage) |
| **Medium** | `type_tool`, `click_tool`, `drag_tool`, `shortcut_tool`, `multi_edit_tool` |
| **Low** | `scroll_tool`, `move_tool`, `wait_tool`, `scrape_tool`, `done_tool` |

### 3. Tool-Specific Approval

Require approval only for specific tools:

```python
agent = Agent(
    llm=llm,
    enable_hitl=True,
    hitl_require_approval_for={"shell_tool", "app_tool"}
)
```

This overrides risk-based approval and only checks the specified tools.

### 4. Custom Approval Logic

Implement custom approval logic for advanced use cases:

```python
from windows_use.agent.hitl.views import ApprovalRequest, ApprovalResponse, ApprovalResult
import time

def my_custom_approver(request: ApprovalRequest) -> ApprovalResponse:
    """Custom approval logic."""

    # Block all shell commands
    if request.tool_name == "shell_tool":
        return ApprovalResponse(
            result=ApprovalResult.REJECTED,
            message="Shell commands blocked by policy",
            approved_by="security_policy",
            timestamp=time.time()
        )

    # Auto-approve read-only operations
    if request.tool_name in {"scroll_tool", "scrape_tool"}:
        return ApprovalResponse(
            result=ApprovalResult.APPROVED,
            message="Read-only auto-approved",
            approved_by="policy",
            timestamp=time.time()
        )

    # Check external approval system (e.g., database, API)
    if check_external_approval_system(request):
        return ApprovalResponse(
            result=ApprovalResult.APPROVED,
            message="Approved by external system",
            approved_by="external_system",
            timestamp=time.time()
        )

    # Default: reject
    return ApprovalResponse(
        result=ApprovalResult.REJECTED,
        message="Not approved by policy",
        approved_by="policy",
        timestamp=time.time()
    )

agent = Agent(
    llm=llm,
    enable_hitl=True,
    hitl_custom_approver=my_custom_approver
)
```

## Complete Parameter Reference

```python
agent = Agent(
    llm=llm,

    # HITL Configuration
    enable_hitl=False,                    # Enable/disable HITL (default: False)
    hitl_backend=ApprovalBackend.CLI,     # Approval backend (CLI, SLACK, AUTO_APPROVE)
    hitl_require_approval_for=None,       # Set of tool names (None = use risk level)
    hitl_min_risk_level="high",           # Minimum risk level ("low", "medium", "high", "critical")
    hitl_slack_webhook_url=None,          # Slack webhook URL (required for Slack backend)
    hitl_slack_token=None,                # Slack bot token (optional, for interactive messages)
    hitl_custom_approver=None,            # Custom approval function
)
```

## Examples

See `examples/hitl_example.py` for complete working examples:

1. **Basic CLI Approval**: Simple interactive approval
2. **Approve All Tools**: Maximum safety mode
3. **Specific Tools Only**: Cherry-pick tools to approve
4. **Slack Approval**: Integration with Slack
5. **Custom Approval Logic**: Advanced custom rules
6. **HITL Disabled**: Default behavior (no approval)

Run examples:

```bash
python examples/hitl_example.py
```

## Best Practices

### 1. Start with High Risk Only

Begin with minimal approvals and expand as needed:

```python
# Good starting point
hitl_min_risk_level="high"  # Only critical/high risk

# If you need more control
hitl_min_risk_level="medium"

# Maximum safety (can be tedious)
hitl_min_risk_level="low"
```

### 2. Use Custom Approvers for Policies

Implement organizational policies in custom approvers:

```python
def corporate_approver(request):
    # Check against corporate policy database
    # Log all requests for audit trail
    # Integrate with ticketing system
    # etc.
    pass
```

### 3. Slack for Remote Monitoring

Use Slack backend when you want to monitor agent remotely:

```python
hitl_backend=ApprovalBackend.SLACK,
hitl_slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL")
```

### 4. Testing Mode

Use AUTO_APPROVE for testing:

```python
# Testing/development
hitl_backend=ApprovalBackend.AUTO_APPROVE

# Production
hitl_backend=ApprovalBackend.CLI
```

### 5. Audit Logging

Custom approvers can log all decisions:

```python
def logging_approver(request):
    # Log to database
    db.log_approval_request(
        tool=request.tool_name,
        params=request.parameters,
        timestamp=time.time()
    )

    # Then delegate to actual approval logic
    return actual_approval_logic(request)
```

## Integration with Other Systems

### Database Logging

```python
import sqlite3

def db_approver(request):
    conn = sqlite3.connect("approvals.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO approval_requests
        (tool_name, parameters, step, timestamp)
        VALUES (?, ?, ?, ?)
    """, (
        request.tool_name,
        str(request.parameters),
        request.step_number,
        time.time()
    ))

    conn.commit()
    conn.close()

    # Continue with approval logic
    return CLIApprovalBackend().request_approval(request)
```

### REST API Integration

```python
import requests

def api_approver(request):
    # Send to approval API
    response = requests.post(
        "https://api.company.com/approvals",
        json={
            "tool": request.tool_name,
            "params": request.parameters,
            "risk": request.risk_level
        }
    )

    if response.json()["approved"]:
        return ApprovalResponse(
            result=ApprovalResult.APPROVED,
            approved_by="api",
            timestamp=time.time()
        )
    else:
        return ApprovalResponse(
            result=ApprovalResult.REJECTED,
            approved_by="api",
            timestamp=time.time()
        )
```

## Troubleshooting

### HITL Not Prompting

Check that HITL is enabled and tool meets criteria:

```python
# Ensure enable_hitl=True
agent = Agent(llm=llm, enable_hitl=True)

# Check risk level includes your tool
# If tool is low risk, set min to "low"
hitl_min_risk_level="low"
```

### Slack Not Working

1. Verify webhook URL is correct
2. Check network connectivity
3. Note: Interactive buttons not yet fully implemented (falls back to CLI)

### Custom Approver Errors

Ensure your custom approver:
- Returns `ApprovalResponse` object
- Handles all edge cases
- Doesn't raise exceptions

```python
def safe_approver(request):
    try:
        # Your logic
        return approval_response
    except Exception as e:
        # Log error and reject by default
        logger.error(f"Approver error: {e}")
        return ApprovalResponse(
            result=ApprovalResult.REJECTED,
            message=f"Approval error: {e}",
            timestamp=time.time()
        )
```

## Security Considerations

### HITL is NOT a Security Sandbox

HITL provides approval workflow but does **NOT**:
- Sandbox or isolate the agent
- Prevent malicious LLM behavior
- Replace proper security practices

### Best Practices

1. **Use in isolated environments** (VM, Windows Sandbox)
2. **Review all high-risk operations** carefully
3. **Implement audit logging** for compliance
4. **Use least privilege** - run agent with minimal permissions
5. **Test thoroughly** before production use

### When to Use HITL

- ✅ Learning how the agent works
- ✅ Production environments with human oversight
- ✅ Compliance requirements
- ✅ High-risk operations
- ✅ Debugging agent behavior

### When NOT to Use HITL

- ❌ As sole security measure
- ❌ Fully automated workflows (defeats purpose)
- ❌ Time-critical operations (approval adds latency)

## API Reference

### `HITLApprovalService`

Main service class for HITL approval.

```python
from windows_use.agent.hitl.service import HITLApprovalService
from windows_use.agent.hitl.views import ApprovalBackend

service = HITLApprovalService(
    backend=ApprovalBackend.CLI,
    require_approval_for=None,
    min_risk_level="high",
    slack_webhook_url=None,
    slack_token=None,
    custom_approver=None
)
```

### `ApprovalRequest`

Data model for approval request.

```python
from windows_use.agent.hitl.views import ApprovalRequest

request = ApprovalRequest(
    tool_name="click_tool",
    tool_description="Click at coordinates",
    parameters={"x": 100, "y": 200},
    step_number=5,
    context="Clicking submit button",
    risk_level="medium"
)
```

### `ApprovalResponse`

Data model for approval response.

```python
from windows_use.agent.hitl.views import ApprovalResponse, ApprovalResult

response = ApprovalResponse(
    result=ApprovalResult.APPROVED,  # or REJECTED, TIMEOUT
    message="Approved by user",
    approved_by="human",
    timestamp=123.45
)
```

### `get_tool_risk_level()`

Get risk level for a tool.

```python
from windows_use.agent.hitl.service import get_tool_risk_level

risk = get_tool_risk_level("shell_tool")  # Returns "critical"
```

## Contributing

To add new approval backends or improve HITL:

1. See `windows_use/agent/hitl/service.py`
2. Implement approval backend class
3. Add tests in `tests/unit/agent/test_hitl.py`
4. Update this documentation

## License

HITL system is part of Windows-Use and covered by the MIT license.

---

**Questions or Issues?**

- GitHub Issues: https://github.com/CursorTouch/Windows-Use/issues
- Discord: https://discord.com/invite/Aue9Yj2VzS
