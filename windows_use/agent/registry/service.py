from windows_use.agent.registry.views import ToolResult
from windows_use.agent.desktop.service import Desktop
from windows_use.agent.hitl.service import HITLApprovalService
from windows_use.agent.hitl.views import ApprovalResult
from windows_use.tool import Tool
from textwrap import dedent
import json
import logging

logger = logging.getLogger(__name__)


class Registry:
    def __init__(self, tools: list[Tool] = [], hitl_service: HITLApprovalService | None = None):
        self.tools = tools
        self.tools_registry = self.registry()
        self.hitl_service = hitl_service

    def tool_prompt(self, tool_name: str) -> str:
        tool = self.tools_registry.get(tool_name)
        if tool is None:
            return f"Tool '{tool_name}' not found."
        return dedent(f"""
        Tool Name: {tool.name}
        Tool Description: {tool.description}
        Tool Schema: {json.dumps(tool.args_schema,indent=4)}
        """)

    def registry(self):
        return {tool.name: tool for tool in self.tools}
    
    def get_tools_prompt(self) -> str:
        tools_prompt = [self.tool_prompt(tool.name) for tool in self.tools]
        return '\n\n'.join(tools_prompt)
    
    def execute(
        self,
        tool_name: str,
        desktop: Desktop | None = None,
        step_number: int = 0,
        **kwargs,
    ) -> ToolResult:
        tool = self.tools_registry.get(tool_name)
        if tool is None:
            return ToolResult(is_success=False, error=f"Tool '{tool_name}' not found.")

        # Check if HITL approval is required
        if self.hitl_service is not None:
            approval_response = self.hitl_service.request_approval(
                tool_name=tool_name,
                tool_description=tool.description,
                parameters=kwargs,
                step_number=step_number,
                context=f"Agent requesting to execute {tool_name}",
            )

            if approval_response.result == ApprovalResult.REJECTED:
                logger.warning(
                    f"Tool execution rejected by HITL: {tool_name} - {approval_response.message}"
                )
                return ToolResult(
                    is_success=False,
                    error=f"Tool execution rejected by human approval: {approval_response.message}",
                )
            elif approval_response.result == ApprovalResult.TIMEOUT:
                logger.warning(f"Tool execution timed out: {tool_name}")
                return ToolResult(
                    is_success=False, error="Tool execution approval timed out"
                )

            logger.info(
                f"Tool execution approved by {approval_response.approved_by}: {tool_name}"
            )

        try:
            args = tool.model.model_validate(kwargs)
            content = tool.invoke(**({'desktop': desktop} | args.model_dump()))
            return ToolResult(is_success=True, content=content)
        except Exception as error:
            return ToolResult(is_success=False, error=str(error))