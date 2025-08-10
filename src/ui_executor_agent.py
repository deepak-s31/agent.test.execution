from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Optional, Union

from autogen_core import FunctionCall
from autogen_core.models import (
    AssistantMessage,
    ChatCompletionClient,
    FunctionExecutionResult,
    FunctionExecutionResultMessage,
    LLMMessage,
    SystemMessage,
    UserMessage,
)
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import McpWorkbench


class UIExecutorAgent:
    """Executes high-level UI steps by driving Playwright MCP tools via AutoGen Workbench."""

    def __init__(self, openai_api_key: str, openai_model: str = "gpt-4o-mini") -> None:
        self._openai_api_key = openai_api_key
        self._openai_model = openai_model

    def _build_model_client(self) -> ChatCompletionClient:
        return OpenAIChatCompletionClient(model=self._openai_model, api_key=self._openai_api_key)

    def _build_system_messages(self) -> List[LLMMessage]:
        guidance = (
            "You are a UI executor agent. Use only the available Playwright MCP tools exposed by the workbench. "
            "Execute the provided steps sequentially, reasoning about the page state as needed. "
            "Prefer concise actions and avoid unnecessary DOM dumps. When all steps are complete, provide a short, "
            "clear summary of what was done. If a requested action is not possible with available tools, explain briefly."
        )
        return [SystemMessage(content=guidance)]

    async def execute(self, steps: Union[str, List[Dict[str, Any]]], workbench: McpWorkbench) -> str:
        """Run the tool-call loop to execute steps with the Playwright MCP workbench."""
        model_client = self._build_model_client()

        if isinstance(steps, list):
            steps_text = json.dumps(steps, ensure_ascii=False)
        else:
            steps_text = steps

        user_prompt = (
            "Execute the following UI steps using the available Playwright MCP tools. "
            "Follow them in order and stop when complete. If a step requires a decision (e.g., choose a result), "
            "pick the most reasonable option.\n\n"
            f"UI_STEPS_JSON: {steps_text}"
        )

        messages: List[LLMMessage] = []
        messages.extend(self._build_system_messages())
        messages.append(UserMessage(content=user_prompt, source="user"))

        create_result = await model_client.create(
            messages=messages,
            tools=(await workbench.list_tools()),
        )

        while isinstance(create_result.content, list) and all(isinstance(c, FunctionCall) for c in create_result.content):
            messages.append(AssistantMessage(content=create_result.content, source="assistant"))

            results: List[FunctionExecutionResult] = []
            for call in create_result.content:
                args = json.loads(call.arguments) if call.arguments else {}
                tool_result = await workbench.call_tool(call.name, arguments=args)
                results.append(
                    FunctionExecutionResult(
                        call_id=call.id,
                        content=tool_result.to_text(),
                        is_error=tool_result.is_error,
                        name=tool_result.name,
                    )
                )

            messages.append(FunctionExecutionResultMessage(content=results))

            create_result = await model_client.create(
                messages=messages,
                tools=(await workbench.list_tools()),
            )

        assert isinstance(create_result.content, str)
        messages.append(AssistantMessage(content=create_result.content, source="assistant"))
        return create_result.content
