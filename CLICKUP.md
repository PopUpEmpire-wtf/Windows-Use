# ClickUp Integration for Windows-Use

This document explains how to connect the Windows-Use agent to a ClickUp workspace so that AI-powered Windows automation can be triggered directly from ClickUp tasks and comments.

---

## Overview

The integration runs a lightweight FastAPI webhook server. ClickUp sends HTTP POST requests to this server whenever configured workspace events occur. The Windows-Use agent processes the request and posts the result back as a ClickUp comment.

### Supported triggers

| Trigger | Behaviour |
|---------|-----------|
| **Task created** with the configured tag (default: `windows-agent`) | The agent processes the task name / description. |
| **Comment posted** starting with `@windows-agent` | The agent processes the text that follows the mention. |

---

## Prerequisites

- Python 3.13+
- A ClickUp workspace with admin access
- A public URL for the webhook server (e.g. via [ngrok](https://ngrok.com) for local development)
- At least one LLM API key (Anthropic, OpenAI, Google, Mistral, Groq, or a local Ollama instance)

---

## Setup

### 1. Install dependencies

```bash
uv add windows-use fastapi uvicorn
```

Or with pip:

```bash
pip install windows-use fastapi uvicorn
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and fill in the required values:

```bash
cp .env.example .env
```

**Required:**

| Variable | Description |
|----------|-------------|
| `CLICKUP_API_KEY` | Personal API token from *ClickUp → Settings → Apps* |

**Optional:**

| Variable | Default | Description |
|----------|---------|-------------|
| `CLICKUP_WEBHOOK_SECRET` | *(none)* | Shared secret for HMAC signature verification |
| `CLICKUP_TASK_TAG` | `windows-agent` | Tag name that marks tasks for the agent |
| `CLICKUP_BOT_NAME` | `windows-agent` | Mention name used in comments (without `@`) |
| `CLICKUP_WEBHOOK_HOST` | `0.0.0.0` | Host to bind the webhook server to |
| `CLICKUP_WEBHOOK_PORT` | `8000` | Port for the webhook server |

**LLM API key** (set at least one):

| Variable | Provider |
|----------|----------|
| `ANTHROPIC_API_KEY` | Anthropic (Claude) |
| `OPENAI_API_KEY` | OpenAI (GPT) |
| `GOOGLE_API_KEY` | Google (Gemini) |
| `MISTRAL_API_KEY` | Mistral |
| `GROQ_API_KEY` | Groq |
| `OLLAMA_BASE_URL` | Local Ollama |

### 3. Register a webhook in ClickUp

1. Go to **ClickUp → Settings → Integrations → Webhooks**.
2. Click **+ New Webhook**.
3. Enter your public webhook URL: `https://<your-server>/webhook`
4. Select the following events:
   - **Task created** (`taskCreated`)
   - **Task comment posted** (`taskCommentPosted`)
5. (Optional) Copy the generated **Signing Secret** into `CLICKUP_WEBHOOK_SECRET`.
6. Save the webhook.

> **Local development tip:**  Use [ngrok](https://ngrok.com) to expose your local server:
> ```bash
> ngrok http 8000
> ```
> Then use the forwarding URL (e.g. `https://abc123.ngrok.io/webhook`) in ClickUp.

### 4. Start the agent

```bash
python clickup_bot.py
```

---

## Usage

### Trigger via a new task

1. Create a task in any ClickUp list.
2. Add the tag **`windows-agent`** (or whatever you set in `CLICKUP_TASK_TAG`).
3. The agent will execute the task name / description and post the result as a comment.

### Trigger via a comment

1. Open any ClickUp task.
2. Post a comment that starts with `@windows-agent`:

   ```
   @windows-agent open Notepad and type "Hello from ClickUp"
   ```

3. The agent will execute the request and reply with the result.

---

## Programmatic usage

You can also embed the integration in your own Python application:

```python
from windows_use.clickup import ClickUpAgent
from windows_use.llms.google import ChatGoogle
from dotenv import load_dotenv
import os

load_dotenv()

llm = ChatGoogle(model="gemini-2.5-flash", api_key=os.getenv("GOOGLE_API_KEY"))

agent = ClickUpAgent(
    llm=llm,
    clickup_api_key=os.getenv("CLICKUP_API_KEY"),
    webhook_secret=os.getenv("CLICKUP_WEBHOOK_SECRET"),
    task_tag="windows-agent",
    bot_name="windows-agent",
)

agent.start(port=8000)
```

---

## Architecture

```
ClickUp  ──POST /webhook──►  FastAPI server (ClickUpAgent)
                                      │
                              WebhookHandler
                            ┌─────────┴──────────┐
                      taskCreated          taskCommentPosted
                            │                    │
                    Check task tag       Check @bot_name
                            │                    │
                      ┌─────▼────────────────────▼─────┐
                      │       Windows-Use Agent         │
                      └─────────────┬───────────────────┘
                                    │
                          Post result comment
                                    │
                             ClickUp API
```

---

## Security

- **Signature verification:** Set `CLICKUP_WEBHOOK_SECRET` to enable HMAC-SHA256 verification of all incoming webhook requests. Requests with an invalid signature are rejected with `401 Unauthorized`.
- **Tag/mention gating:** The agent only processes tasks with the sentinel tag and comments that explicitly mention the bot, preventing accidental execution.
- **Thread locking:** A mutex ensures only one agent execution runs at a time.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `CLICKUP_API_KEY is required` | Set the `CLICKUP_API_KEY` environment variable. |
| Webhook returns `401 Unauthorized` | Ensure `CLICKUP_WEBHOOK_SECRET` matches the secret in ClickUp. |
| Agent not triggered on task creation | Verify the task has the correct tag (exact match, case-insensitive). |
| Agent not triggered on comment | Ensure the comment starts with `@windows-agent` (no leading spaces). |
| Port already in use | Change `CLICKUP_WEBHOOK_PORT` in `.env`. |

---

## Related

- [Windows-Use README](README.md)
- [ClickUp API documentation](https://clickup.com/api)
- [ClickUp Webhooks guide](https://clickup.com/api/clickupreference/operation/CreateWebhook/)
