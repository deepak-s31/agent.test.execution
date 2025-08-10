import asyncio
import json
import os
import sys
from typing import Any, List, Union

from dotenv import load_dotenv
from autogen_ext.tools.mcp import McpWorkbench, SseServerParams

# Ensure local imports work when running as a script
sys.path.append(os.path.dirname(__file__))
from ui_executor_agent import UIExecutorAgent  # noqa: E402


def _read_steps_from_env() -> Union[str, List[Any]]:
    steps_file = os.getenv("UI_STEPS_FILE")
    steps_text = os.getenv("UI_STEPS")

    if steps_file and os.path.exists(steps_file):
        with open(steps_file, "r", encoding="utf-8") as f:
            data = f.read().strip()
    elif steps_text:
        data = steps_text.strip()
    else:
        raise RuntimeError("Provide UI steps via UI_STEPS or UI_STEPS_FILE in the environment.")

    try:
        return json.loads(data)
    except Exception:
        return data


async def amain() -> None:
    load_dotenv()

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required in environment or .env file")

    openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    mcp_sse_url = os.getenv("PLAYWRIGHT_MCP_SSE_URL", "http://localhost:8931/sse")

    steps = _read_steps_from_env()

    agent = UIExecutorAgent(openai_api_key=openai_api_key, openai_model=openai_model)

    server_params = SseServerParams(url=mcp_sse_url)
    async with McpWorkbench(server_params) as workbench:  # type: ignore
        result = await agent.execute(steps=steps, workbench=workbench)
        print("\n=== Final Result ===\n")
        print(result)


if __name__ == "__main__":
    asyncio.run(amain())
