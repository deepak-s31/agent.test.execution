# UI Executor Agent (AutoGen + Playwright MCP)

This project executes high-level UI steps using AutoGen's Workbench with a Playwright MCP server.

- Docs used: [AutoGen Workbench (and MCP)](https://microsoft.github.io/autogen/stable//user-guide/core-user-guide/components/workbench.html)

## Prerequisites
- Python 3.9+
- Node.js (to run the Playwright MCP server)

## Install
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Start Playwright MCP
Install Chrome for Playwright and run the MCP server in another terminal:
```bash
npx playwright install chrome
npx @playwright/mcp@latest --port 8931
```

## Configure
Create your `.env` from the example and set your OpenAI key:
```bash
cp .env.example .env
# edit .env to add OPENAI_API_KEY and your UI steps
```

## Run
```bash
python src/main.py
```

The agent will connect to the Playwright MCP server over SSE and use the available tools to execute your steps. It follows the Workbench tool-call loop pattern from the docs and stops when it reaches a final answer.

