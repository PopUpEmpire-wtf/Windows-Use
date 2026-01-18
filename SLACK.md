# Slack Integration for Windows-Use

Connect your Windows-Use agent to Slack and control Windows automation directly from your Slack workspace!

## Features

- 🤖 Control Windows automation through Slack messages
- 💬 Three ways to interact: Direct Messages, @mentions, and slash commands
- ⚡ Real-time task execution with status updates
- 🔒 Thread-safe execution (one task at a time)
- 📊 Built-in status and help commands

## Prerequisites

1. **Windows-Use installed** - Follow the main README for installation
2. **Slack workspace** - Admin access to create apps
3. **LLM API key** - Any supported provider (Claude, OpenAI, Gemini, etc.)

## Setup Instructions

### Step 1: Create a Slack App

1. Go to [Slack API Dashboard](https://api.slack.com/apps)
2. Click **"Create New App"** → **"From scratch"**
3. Enter app name (e.g., "Windows-Use Agent") and select your workspace
4. Click **"Create App"**

### Step 2: Configure Bot Permissions

1. In your app settings, go to **"OAuth & Permissions"**
2. Scroll to **"Scopes"** → **"Bot Token Scopes"**
3. Add the following scopes:
   - `app_mentions:read` - Read messages that mention your bot
   - `chat:write` - Send messages as the bot
   - `im:history` - View messages in direct messages
   - `im:read` - View basic info about direct messages
   - `im:write` - Start direct messages with users
   - `channels:history` - View messages in public channels (optional)
   - `groups:history` - View messages in private channels (optional)

4. Scroll to top and click **"Install to Workspace"**
5. Authorize the app
6. Copy the **"Bot User OAuth Token"** (starts with `xoxb-`)
   - Save this as `SLACK_BOT_TOKEN` in your `.env` file

### Step 3: Enable Socket Mode

1. Go to **"Socket Mode"** in the left sidebar
2. Enable Socket Mode
3. You'll be prompted to create an app-level token:
   - Token Name: `websocket-token` (or any name)
   - Scope: `connections:write`
4. Click **"Generate"**
5. Copy the **App-Level Token** (starts with `xapp-`)
   - Save this as `SLACK_APP_TOKEN` in your `.env` file

### Step 4: Enable Event Subscriptions

1. Go to **"Event Subscriptions"** in the left sidebar
2. Enable Events
3. Under **"Subscribe to bot events"**, add:
   - `app_mention` - Bot is mentioned
   - `message.im` - Direct messages to the bot

4. Click **"Save Changes"**

### Step 5: Configure Slash Commands (Optional)

1. Go to **"Slash Commands"** in the left sidebar
2. Click **"Create New Command"**
3. Create the following commands:

   **Command 1: /windows**
   - Command: `/windows`
   - Request URL: (leave blank for Socket Mode)
   - Short Description: `Execute a Windows automation task`
   - Usage Hint: `open notepad and type hello`

   **Command 2: /windows-help**
   - Command: `/windows-help`
   - Request URL: (leave blank for Socket Mode)
   - Short Description: `Show Windows-Use help`

   **Command 3: /windows-status**
   - Command: `/windows-status`
   - Request URL: (leave blank for Socket Mode)
   - Short Description: `Check agent status`

4. Click **"Save"**

### Step 6: Configure Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your tokens:
   ```env
   # Slack tokens
   SLACK_BOT_TOKEN=xoxb-your-bot-token-here
   SLACK_APP_TOKEN=xapp-your-app-token-here

   # LLM API key (choose one)
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   # or
   OPENAI_API_KEY=sk-your-key-here
   # or
   GOOGLE_API_KEY=your-key-here
   ```

### Step 7: Install Dependencies

```bash
pip install -e .
# or
pip install slack-bolt python-dotenv
```

### Step 8: Run the Slack Bot

```bash
python slack_bot.py
```

You should see:
```
🚀 Starting Windows-Use Slack Agent...
🔧 Initializing LLM...
✓ Using AnthropicLLM
🔧 Initializing Slack agent...
✓ Slack agent initialized

==================================================
🤖 Windows-Use Slack Agent is now running!
==================================================
```

## Usage

### Method 1: Direct Message

1. Open Slack
2. Find your bot in the "Apps" section
3. Send a direct message with your task:
   ```
   open notepad and type hello world
   ```

### Method 2: @Mention in Channel

1. Invite the bot to a channel: `/invite @Windows-Use Agent`
2. Mention the bot with your task:
   ```
   @Windows-Use Agent take a screenshot and save it
   ```

### Method 3: Slash Commands

Use the `/windows` command:
```
/windows launch calculator and compute 5 + 7
```

Other commands:
- `/windows-help` - Show help and available commands
- `/windows-status` - Check if the agent is busy

## Example Tasks

```
open chrome and search for python tutorial
```

```
create a new folder called Projects on desktop
```

```
launch notepad, type my todo list, and save as todo.txt
```

```
take a screenshot and upload it
```

```
open settings and change wallpaper
```

## Architecture

The Slack integration wraps the existing Windows-Use agent:

```
Slack Message
    ↓
SlackAgent (service.py)
    ↓
MessageHandler/CommandHandler (handlers.py)
    ↓
Windows-Use Agent (agent/service.py)
    ↓
Desktop Tools (click, type, etc.)
    ↓
Windows UI Automation
    ↓
Result sent back to Slack
```

## API Reference

### SlackAgent Class

```python
from windows_use.slack import SlackAgent
from windows_use.llms.anthropic import AnthropicLLM

# Initialize
llm = AnthropicLLM(api_key="your-key")
agent = SlackAgent(
    llm=llm,
    slack_bot_token="xoxb-...",  # Optional if in env
    slack_app_token="xapp-...",  # Optional if in env
    browser="chrome",  # Optional: browser choice
    vision=True,  # Optional: enable vision mode
)

# Start the agent
agent.start()
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SLACK_BOT_TOKEN` | Yes | Bot OAuth token (xoxb-...) |
| `SLACK_APP_TOKEN` | Yes | App-level token (xapp-...) |
| `ANTHROPIC_API_KEY` | One of | Claude API key |
| `OPENAI_API_KEY` | these | OpenAI API key |
| `GOOGLE_API_KEY` | required | Google Gemini API key |
| `MISTRAL_API_KEY` | | Mistral API key |
| `GROQ_API_KEY` | | Groq API key |
| `OLLAMA_BASE_URL` | | Ollama base URL |

## Troubleshooting

### Bot doesn't respond

1. Check that Socket Mode is enabled
2. Verify both tokens are correct in `.env`
3. Make sure the bot is invited to the channel (for mentions)
4. Check console output for errors

### "Missing scope" error

Go to OAuth & Permissions and add the required scopes listed in Step 2.

### LLM initialization fails

Make sure you have set one of the LLM API keys in your `.env` file.

### Agent is slow

- The agent executes tasks sequentially for safety
- Check your LLM provider's rate limits
- Consider using a faster model (e.g., Gemini Flash, GPT-4o Mini)

## Security Considerations

⚠️ **Important Security Notes:**

1. **Access Control**: The bot can execute ANY Windows command. Only install in trusted workspaces.
2. **Token Security**: Keep your `.env` file private. Never commit it to version control.
3. **Task Validation**: Review tasks before execution in production environments.
4. **Network**: The bot uses Socket Mode (websocket) - no public URL needed.
5. **Permissions**: The agent runs with the permissions of the user running `slack_bot.py`.

## Advanced Configuration

### Custom Agent Configuration

```python
agent = SlackAgent(
    llm=llm,
    browser="edge",  # Chrome, Edge, or Firefox
    vision=True,  # Enable screenshot analysis
    # Add other Agent parameters...
)
```

### Running as a Service

**Windows (using NSSM):**
```bash
nssm install WindowsUseSlack python C:\path\to\slack_bot.py
nssm start WindowsUseSlack
```

**Linux/WSL (using systemd):**
Create `/etc/systemd/system/windows-use-slack.service`:
```ini
[Unit]
Description=Windows-Use Slack Agent
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/Windows-Use
ExecStart=/usr/bin/python3 /path/to/Windows-Use/slack_bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable windows-use-slack
sudo systemctl start windows-use-slack
```

## Contributing

Found a bug or have a feature request? Open an issue on [GitHub](https://github.com/CursorTouch/Windows-Use).

## License

MIT License - Same as Windows-Use main project
