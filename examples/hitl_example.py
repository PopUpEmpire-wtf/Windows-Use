"""
Example: Using Human-In-The-Loop (HITL) Approval System

This example demonstrates how to enable and configure the HITL approval system
for Windows-Use agent. HITL allows you to approve or reject tool executions
before they are performed, adding an extra layer of control and safety.
"""

from windows_use.agent import Agent, Browser
from windows_use.agent.hitl.views import ApprovalBackend, ApprovalRequest, ApprovalResponse, ApprovalResult
from windows_use.llms.anthropic import ChatAnthropic
from dotenv import load_dotenv
import os

load_dotenv()


def example_1_basic_cli_approval():
    """
    Example 1: Basic HITL with CLI approval

    This configuration:
    - Enables HITL with CLI backend (interactive terminal prompts)
    - Requires approval for high-risk and critical tools only
    - Low/medium risk tools auto-approve
    """
    print("\n=== Example 1: Basic CLI Approval ===")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    llm = ChatAnthropic(model="claude-sonnet-4-5", api_key=api_key, temperature=0.7)

    agent = Agent(
        llm=llm,
        browser=Browser.EDGE,
        use_vision=False,
        enable_hitl=True,  # Enable HITL
        hitl_backend=ApprovalBackend.CLI,  # Use CLI prompts
        hitl_min_risk_level="high",  # Only high/critical tools need approval
    )

    # This will prompt for approval before executing risky commands
    agent.print_response(query="Open notepad and type 'Hello World'")


def example_2_approve_all_tools():
    """
    Example 2: Require approval for ALL tools

    This configuration:
    - Requires approval for every single tool execution
    - Good for highly sensitive environments
    """
    print("\n=== Example 2: Approve All Tools ===")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    llm = ChatAnthropic(model="claude-sonnet-4-5", api_key=api_key, temperature=0.7)

    agent = Agent(
        llm=llm,
        browser=Browser.EDGE,
        use_vision=False,
        enable_hitl=True,
        hitl_backend=ApprovalBackend.CLI,
        hitl_min_risk_level="low",  # All tools require approval
    )

    agent.print_response(query="Scroll down the page")


def example_3_specific_tools():
    """
    Example 3: Approve specific tools only

    This configuration:
    - Only requires approval for shell_tool and app_tool
    - All other tools auto-approve
    """
    print("\n=== Example 3: Specific Tools Only ===")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    llm = ChatAnthropic(model="claude-sonnet-4-5", api_key=api_key, temperature=0.7)

    agent = Agent(
        llm=llm,
        browser=Browser.EDGE,
        use_vision=False,
        enable_hitl=True,
        hitl_backend=ApprovalBackend.CLI,
        hitl_require_approval_for={"shell_tool", "app_tool"},  # Only these tools
    )

    agent.print_response(query="Click the Start button")


def example_4_slack_approval():
    """
    Example 4: Slack approval notifications

    This configuration:
    - Sends approval requests to Slack
    - Falls back to CLI if Slack fails
    - Requires Slack webhook URL
    """
    print("\n=== Example 4: Slack Approval ===")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    slack_webhook = os.getenv("SLACK_WEBHOOK_URL")  # Get from Slack app settings

    if not slack_webhook:
        print("Error: SLACK_WEBHOOK_URL not found in environment variables")
        print("Please set it in your .env file")
        return

    llm = ChatAnthropic(model="claude-sonnet-4-5", api_key=api_key, temperature=0.7)

    agent = Agent(
        llm=llm,
        browser=Browser.EDGE,
        use_vision=False,
        enable_hitl=True,
        hitl_backend=ApprovalBackend.SLACK,
        hitl_slack_webhook_url=slack_webhook,
        hitl_min_risk_level="high",
    )

    agent.print_response(query="Create a new folder on desktop")


def example_5_custom_approval_logic():
    """
    Example 5: Custom approval logic

    This configuration:
    - Uses custom approval function
    - Implements custom business logic
    - Can integrate with external systems
    """
    print("\n=== Example 5: Custom Approval Logic ===")

    def custom_approver(request: ApprovalRequest) -> ApprovalResponse:
        """
        Custom approval logic.

        Example rules:
        - Auto-reject all shell commands
        - Auto-approve read-only operations
        - Require manual approval for everything else
        """
        import time

        # Block all shell commands
        if request.tool_name == "shell_tool":
            print(f"🚫 Custom policy: Blocking shell command: {request.parameters.get('command')}")
            return ApprovalResponse(
                result=ApprovalResult.REJECTED,
                message="Shell commands are blocked by security policy",
                approved_by="security_policy",
                timestamp=time.time(),
            )

        # Auto-approve read-only operations
        if request.tool_name in {"scroll_tool", "wait_tool", "scrape_tool"}:
            print(f"✅ Custom policy: Auto-approving read-only operation: {request.tool_name}")
            return ApprovalResponse(
                result=ApprovalResult.APPROVED,
                message="Read-only operation auto-approved",
                approved_by="security_policy",
                timestamp=time.time(),
            )

        # For everything else, ask the user
        print(f"\n⚠️  Custom approval required for: {request.tool_name}")
        print(f"   Parameters: {request.parameters}")
        choice = input("Approve? (y/n): ").strip().lower()

        if choice == "y":
            return ApprovalResponse(
                result=ApprovalResult.APPROVED,
                message="Approved by user via custom policy",
                approved_by="human",
                timestamp=time.time(),
            )
        else:
            return ApprovalResponse(
                result=ApprovalResult.REJECTED,
                message="Rejected by user via custom policy",
                approved_by="human",
                timestamp=time.time(),
            )

    api_key = os.getenv("ANTHROPIC_API_KEY")
    llm = ChatAnthropic(model="claude-sonnet-4-5", api_key=api_key, temperature=0.7)

    agent = Agent(
        llm=llm,
        browser=Browser.EDGE,
        use_vision=False,
        enable_hitl=True,
        hitl_backend=ApprovalBackend.CLI,
        hitl_min_risk_level="low",  # Check all tools
        hitl_custom_approver=custom_approver,  # Use custom logic
    )

    agent.print_response(query="Open calculator")


def example_6_disabled_hitl():
    """
    Example 6: HITL Disabled (default behavior)

    This is the default - no approval required for any tool.
    Good for trusted environments or testing.
    """
    print("\n=== Example 6: HITL Disabled (Default) ===")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    llm = ChatAnthropic(model="claude-sonnet-4-5", api_key=api_key, temperature=0.7)

    agent = Agent(
        llm=llm,
        browser=Browser.EDGE,
        use_vision=False,
        enable_hitl=False,  # HITL disabled (default)
    )

    agent.print_response(query="What time is it?")


def main():
    """Run HITL examples."""
    print("=" * 60)
    print("Windows-Use HITL (Human-In-The-Loop) Examples")
    print("=" * 60)

    examples = {
        "1": ("Basic CLI Approval", example_1_basic_cli_approval),
        "2": ("Approve All Tools", example_2_approve_all_tools),
        "3": ("Specific Tools Only", example_3_specific_tools),
        "4": ("Slack Approval", example_4_slack_approval),
        "5": ("Custom Approval Logic", example_5_custom_approval_logic),
        "6": ("HITL Disabled", example_6_disabled_hitl),
    }

    print("\nAvailable examples:")
    for key, (name, _) in examples.items():
        print(f"  {key}. {name}")

    choice = input("\nSelect an example (1-6): ").strip()

    if choice in examples:
        _, example_func = examples[choice]
        example_func()
    else:
        print("Invalid choice. Please run again and select 1-6.")


if __name__ == "__main__":
    main()
