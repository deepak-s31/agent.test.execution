# UI Executor Agent (AutoGen + Playwright MCP)

Execute high‑level UI automation steps by combining AutoGen's Workbench with a Playwright MCP server. The agent reads your steps (JSON or text), connects to the MCP server over SSE, and drives the browser using the exposed Playwright tools.

- Reference: [AutoGen Workbench (with MCP)](https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/components/workbench.html)

### How it works
- `src/ui_executor_agent.py` builds a minimal tool‑calling loop using AutoGen Workbench and an OpenAI chat model.
- `src/main.py` loads environment variables, reads your UI steps from `UI_STEPS` or `UI_STEPS_FILE`, connects to the Playwright MCP server (`/sse`), and runs the loop until a final answer is produced.
- The MCP server is provided by `@playwright/mcp` (Node), which exposes Playwright actions as MCP tools.

## Prerequisites
- Python 3.9–3.12 (CI uses 3.11)
- Node.js 18+ (CI uses Node 20)
- For browser control: Playwright browsers installed locally

## Install (Python)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Start the Playwright MCP server
Run this in a separate terminal before you start the Python agent.
```bash
# Install required browser(s)
npx playwright install chrome

# Start the MCP server (listens on :8931 by default below)
npx @playwright/mcp@latest --port 8931
```

## Configure environment
You can use a `.env` file or export variables in your shell. The agent uses sensible defaults for optional values.

Required:
- `OPENAI_API_KEY`: your OpenAI API key

Optional (defaults shown):
- `OPENAI_MODEL`: `gpt-4o-mini`
- `PLAYWRIGHT_MCP_SSE_URL`: `http://localhost:8931/sse`
- `UI_STEPS`: JSON string or free‑form text describing steps
- `UI_STEPS_FILE`: path to a file containing the steps (JSON or text)

Example `.env`:
```ini
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
PLAYWRIGHT_MCP_SSE_URL=http://localhost:8931/sse

# Provide steps via env (alternative is UI_STEPS_FILE)
UI_STEPS=[
  {"action":"goto","url":"https://example.com"},
  {"action":"wait_for","state":"networkidle"},
  {"action":"screenshot","path":"ui-executor-screenshot.png"}
]
```

## Providing UI steps
You can provide steps as:
- JSON list (recommended): see the example above; this is what CI uses
- Free‑form text instructions: the model will interpret and plan with available tools
- File: point `UI_STEPS_FILE` to a path containing either JSON or text

Notes:
- If both `UI_STEPS_FILE` and `UI_STEPS` are set, the file wins.
- If neither is provided, the program will error with a clear message.

## Run locally
With the MCP server running in another terminal:
```bash
python src/main.py
```

The agent connects to the MCP server via SSE and executes the steps, calling the available tools until completion. A short summary is printed at the end, and any files created by tools (e.g., screenshots) are written to the working directory.

## CI workflow
This repo includes a GitHub Actions workflow at `.github/workflows/ui-executor.yml` that:
- Sets up Python and Node
- Installs Playwright deps and the `@playwright/mcp` server
- Starts the MCP server on port 8931 and waits for readiness
- Runs `python src/main.py` with `UI_STEPS` provided via workflow env
- Uploads artifacts like `ui-executor-screenshot.png` and `mcp.log`

To run in your fork, add `OPENAI_API_KEY` as a repository secret. You can trigger the workflow on push or manually via the Actions tab.

## Project structure
- `src/main.py`: entry point; environment loading, step ingestion, workbench setup
- `src/ui_executor_agent.py`: model client and tool‑calling loop using AutoGen
- `requirements.txt`: Python dependencies (AutoGen core/ext, OpenAI SDK, dotenv, rich)

## Troubleshooting
- MCP server not reachable: ensure it’s running (`npx @playwright/mcp@latest --port 8931`) and that `PLAYWRIGHT_MCP_SSE_URL` matches (`/sse`).
- Missing OpenAI key: set `OPENAI_API_KEY` in `.env` or your shell.
- Steps parsing errors: if using JSON in `UI_STEPS`/file, ensure the content is valid JSON. Otherwise, provide plain text and let the model plan.
- Playwright browser missing: run `npx playwright install chrome` (or install `chromium`/`firefox`/`webkit` as needed).

## Extending
- System guidance lives in `UIExecutorAgent._build_system_messages`. Adjust to change behavior (verbosity, decision‑making).
- Add new tools by extending the MCP server or pointing the agent at an MCP server exposing additional capabilities.

## License
No license provided. Add a `LICENSE` file to specify terms if you plan to distribute.
