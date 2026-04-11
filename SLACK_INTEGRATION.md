# Slack Integration Guide

## Overview

The Windows-Use agent now includes comprehensive Slack integration, allowing you to receive real-time notifications about agent activities, tool executions, and system events directly in your Slack workspace.

## Features

- **Agent Progress Tracking**: Real-time updates on agent steps and thoughts
- **Tool Execution Notifications**: Detailed reports on tool usage and results
- **Error Notifications**: Immediate alerts when errors occur
- **UI Event Monitoring**: Optional notifications for focus and property changes
- **Custom Messages**: LLM can send custom messages to Slack using the Slack Tool
- **Rich Formatting**: Beautiful Slack messages with color coding and structured fields
- **Flexible Configuration**: Control which events trigger notifications

## Quick Start

### 1. Install Slack SDK

The Slack SDK is already included in the project dependencies. If you need to install it manually:

```bash
pip install slack-sdk
```

### 2. Configure Environment Variables

Create or update your `.env` file:

```env
# Enable Slack notifications
SLACK_NOTIFICATIONS_ENABLED=true

# Choose one of these methods:

# Method 1: Incoming Webhook (Recommended for simple setups)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Method 2: Slack Bot Token (For advanced features)
# SLACK_BOT_TOKEN=xoxb-your-bot-token
# SLACK_CHANNEL=#windows-use-agent
```

### 3. Set Up Slack Webhook or Bot

#### Option A: Incoming Webhook (Simpler)

1. Go to [Slack API Apps](https://api.slack.com/apps)
2. Create a new app or select existing app
3. Enable "Incoming Webhooks"
4. Click "Add New Webhook to Workspace"
5. Select the channel to post to
6. Copy the webhook URL to your `.env` file

#### Option B: Slack Bot (More Flexible)

1. Go to [Slack API Apps](https://api.slack.com/apps)
2. Create a new app or select existing app
3. Go to "OAuth & Permissions"
4. Add these bot token scopes:
   - `chat:write`
   - `chat:write.customize`
5. Install the app to your workspace
6. Copy the "Bot User OAuth Token" to your `.env` file
7. Invite the bot to your desired channel: `/invite @YourBotName`

### 4. Run the Agent

That's it! The agent will now send notifications to Slack automatically.

```python
from windows_use.agent import Agent, Browser
from windows_use.llms.anthropic import ChatAnthropic

llm = ChatAnthropic(model="claude-sonnet-4-5", api_key=api_key)
agent = Agent(llm=llm, browser=Browser.EDGE)
agent.print_response(query="Check my email")
```

## Configuration Options

### Notification Preferences

Control which events trigger Slack notifications by setting these environment variables:

```env
# Agent lifecycle notifications (default: true)
NOTIFY_AGENT_START=true
NOTIFY_AGENT_COMPLETE=true

# Tool execution notifications (default: true)
NOTIFY_TOOL_EXECUTION=true

# Error notifications (default: true)
NOTIFY_ERRORS=true

# UI event notifications - can be verbose (default: false)
NOTIFY_UI_EVENTS=false
```

### Channel Configuration

Specify the default channel for notifications:

```env
SLACK_CHANNEL=#windows-use-agent
```

You can override this per-message using the Slack Tool (see below).

## Slack Tool - Custom Messages

The LLM agent can send custom messages to Slack using the built-in Slack Tool.

### Usage in Agent Prompts

The agent automatically has access to the Slack Tool and can use it like this:

```xml
<action_name>Slack Tool</action_name>
<action_input>
{
  "message": "File processing completed successfully!",
  "color": "success",
  "fields": {
    "Files Processed": "42",
    "Total Size": "1.2 GB",
    "Duration": "3.5 minutes"
  }
}
</action_input>
```

### Tool Parameters

- **message** (required): The message text to send
- **channel** (optional): Override default channel (e.g., `"#alerts"`)
- **fields** (optional): Key-value pairs for structured data display
- **color** (optional): Visual color indicator
  - `"success"` - Green
  - `"error"` - Red
  - `"warning"` - Orange
  - `"info"` - Blue (default)

### Example Messages

#### Simple Message
```json
{
  "message": "Task completed successfully!"
}
```

#### Rich Message with Fields
```json
{
  "message": "System health check complete",
  "color": "success",
  "fields": {
    "CPU Usage": "45%",
    "Memory": "8.2 GB / 16 GB",
    "Disk Space": "250 GB free",
    "Status": "Healthy"
  }
}
```

#### Error Notification
```json
{
  "message": "Failed to process file",
  "color": "error",
  "channel": "#alerts",
  "fields": {
    "Error": "FileNotFoundError",
    "Path": "C:\\data\\input.csv"
  }
}
```

## Message Types

The Slack integration automatically sends different types of formatted messages:

### 1. Agent Start Notification

Sent when the agent begins processing a query.

**Includes:**
- Query text
- Model name and provider
- Maximum steps allowed
- Timestamp

**Color:** Blue

### 2. Step Notifications

Sent for each agent step during execution.

**Includes:**
- Current step number (e.g., Step 3/25)
- Agent's thought process
- Next action to execute

**Color:** Blue

### 3. Tool Execution Notifications

Sent when the agent executes a tool.

**Includes:**
- Tool name
- Input parameters (formatted JSON)
- Execution result
- Success/failure status

**Color:** Green (success) or Red (failure)

### 4. Completion Notification

Sent when the agent successfully completes the task.

**Includes:**
- Final answer
- Total steps used
- Completion status

**Color:** Green

### 5. Error Notifications

Sent when errors occur during execution.

**Includes:**
- Error message
- Context information
- Step number where error occurred

**Color:** Red

### 6. UI Event Notifications (Optional)

Sent when UI focus or properties change (disabled by default due to verbosity).

**Includes:**
- Event type (Focus Change, Property Change, Structure Change)
- Application name
- Element details

**Color:** Orange (Structure Change) or Blue (Focus/Property)

## Rate Limiting

To prevent Slack rate limits and message spam, the integration includes:

- **Minimum notification interval**: 1 second between messages
- Automatic debouncing of duplicate UI events
- Configurable event filtering

## Troubleshooting

### No Messages Appearing in Slack

1. **Check if Slack is enabled**:
   ```env
   SLACK_NOTIFICATIONS_ENABLED=true
   ```

2. **Verify webhook URL or bot token** is correct in `.env`

3. **Check logs** for Slack-related errors:
   ```
   [Slack] Webhook client initialized
   [Slack] Message sent via webhook
   ```

4. **Test with simple message**:
   ```python
   from windows_use.slack import SlackIntegration
   
   slack = SlackIntegration()
   success = slack.send_text("Test message")
   print(f"Message sent: {success}")
   ```

### Webhook vs Bot Token

**Webhook URL** format:
```
https://hooks.slack.com/services/YOUR_TEAM_ID/YOUR_CHANNEL_ID/YOUR_WEBHOOK_TOKEN
```

**Bot Token** format:
```
xoxb-YOUR-BOT-TOKEN-HERE-REPLACE-WITH-ACTUAL-TOKEN
```

### Too Many Notifications

If you're receiving too many notifications:

1. **Disable UI events** (most verbose):
   ```env
   NOTIFY_UI_EVENTS=false
   ```

2. **Disable tool execution notifications**:
   ```env
   NOTIFY_TOOL_EXECUTION=false
   ```

3. **Keep only start and completion**:
   ```env
   NOTIFY_AGENT_START=true
   NOTIFY_AGENT_COMPLETE=true
   NOTIFY_TOOL_EXECUTION=false
   NOTIFY_UI_EVENTS=false
   NOTIFY_ERRORS=true
   ```

### Rate Limit Errors

If you hit Slack's rate limits:

- The integration already includes 1-second minimum interval
- Consider disabling verbose notifications (UI events, tool executions)
- Use Bot Token instead of Webhook for better rate limit handling

## Advanced Usage

### Programmatic Configuration

You can configure Slack integration programmatically:

```python
from windows_use.slack import SlackIntegration, SlackNotificationConfig

config = SlackNotificationConfig(
    enabled=True,
    webhook_url="https://hooks.slack.com/services/...",
    channel="#my-channel",
    username="Windows-Use Agent",
    icon_emoji=":robot_face:",
    notify_agent_start=True,
    notify_agent_complete=True,
    notify_tool_execution=True,
    notify_ui_events=False,
    notify_errors=True
)

slack = SlackIntegration(config=config)
```

### Custom Message Formatting

Create custom Slack messages:

```python
from windows_use.slack import format_custom_message, SlackIntegration
from windows_use.slack.config import COLOR_SUCCESS

slack = SlackIntegration()

message = format_custom_message(
    text="Custom notification",
    title="System Alert",
    fields={
        "Status": "Active",
        "Priority": "High"
    },
    color=COLOR_SUCCESS
)

slack.send(message)
```

### Sending to Multiple Channels

Send different notifications to different channels:

```python
from windows_use.slack import SlackMessage

# Send to #general
general_message = SlackMessage(
    text="Public announcement",
    channel="#general"
)
slack.send(general_message)

# Send to #alerts
alert_message = SlackMessage(
    text="Critical error",
    channel="#alerts"
)
slack.send(alert_message)
```

## Architecture

### Module Structure

```
windows_use/slack/
├── __init__.py           # Public API exports
├── service.py            # SlackIntegration class
├── views.py              # Pydantic models
├── config.py             # Configuration constants
└── formatter.py          # Message formatting utilities
```

### Key Components

- **SlackIntegration**: Main service class for sending messages
- **SlackMessage**: Pydantic model for message structure
- **Formatters**: Functions to format agent data into Slack messages
- **Configuration**: Environment-based configuration management

### Integration Points

The Slack integration is woven into the agent at these points:

1. **Agent Initialization**: `Agent.__init__()` creates `SlackIntegration` instance
2. **Agent Start**: `Agent.invoke()` sends start notification
3. **Step Loop**: Each step sends progress notification
4. **Tool Execution**: Tool results trigger execution notifications
5. **Completion**: Success/failure sends final notification
6. **Error Handling**: All error paths send error notifications
7. **UI Events**: Watchdog callbacks can send event notifications

### Message Flow

```
Agent Event
    ↓
Format Message (formatter.py)
    ↓
SlackIntegration.send()
    ↓
Webhook Client OR Bot Client
    ↓
Slack API
    ↓
Slack Channel
```

## Security Considerations

### Protecting Sensitive Data

- **Never commit** `.env` file with Slack credentials
- Use `.gitignore` to exclude `.env` and secrets
- Rotate webhook URLs and bot tokens periodically
- Limit bot permissions to only what's needed (`chat:write`)

### Message Content

- Be aware that agent queries and tool results are sent to Slack
- Avoid sending sensitive information in notifications
- Use private channels for sensitive agent operations
- Consider using Slack's audit log features

### Webhook Security

- Webhook URLs are secret credentials - treat them like passwords
- Anyone with the webhook URL can post to your channel
- Regenerate webhook URLs if accidentally exposed
- Use Bot Tokens for better security controls

## Best Practices

1. **Start Simple**: Begin with default settings, adjust as needed
2. **Use Private Channels**: Create dedicated channels for agent notifications
3. **Monitor Volume**: Start with fewer notifications, add more if useful
4. **Test First**: Use test channels before production
5. **Document Setup**: Keep `.env.example` with non-secret values
6. **Regular Review**: Periodically review notification usefulness

## Example Workflows

### Development Workflow

```env
# .env for development
SLACK_NOTIFICATIONS_ENABLED=true
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/.../dev-channel
NOTIFY_AGENT_START=true
NOTIFY_AGENT_COMPLETE=true
NOTIFY_TOOL_EXECUTION=true
NOTIFY_ERRORS=true
NOTIFY_UI_EVENTS=false  # Too verbose
```

### Production Workflow

```env
# .env for production
SLACK_NOTIFICATIONS_ENABLED=true
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/.../prod-channel
NOTIFY_AGENT_START=true
NOTIFY_AGENT_COMPLETE=true
NOTIFY_TOOL_EXECUTION=false  # Only start/end
NOTIFY_ERRORS=true
NOTIFY_UI_EVENTS=false
```

### Monitoring Workflow

```env
# .env for monitoring only
SLACK_NOTIFICATIONS_ENABLED=true
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/.../monitoring
NOTIFY_AGENT_START=false
NOTIFY_AGENT_COMPLETE=false
NOTIFY_TOOL_EXECUTION=false
NOTIFY_ERRORS=true  # Only errors
NOTIFY_UI_EVENTS=false
```

## FAQ

### Q: Do I need to configure Slack to use the agent?

**A:** No, Slack integration is completely optional. The agent works perfectly without it. Slack notifications are a convenience feature for monitoring agent activities.

### Q: Can I use both webhook and bot token?

**A:** The integration tries webhook first, then bot token. We recommend using only one method to avoid confusion.

### Q: How do I disable Slack after setting it up?

**A:** Set `SLACK_NOTIFICATIONS_ENABLED=false` in your `.env` file, or remove the Slack environment variables.

### Q: Can the agent read messages from Slack?

**A:** Not currently. The integration is one-way (agent → Slack). The agent cannot read or respond to Slack messages.

### Q: Will this slow down the agent?

**A:** Slack notifications are sent asynchronously with rate limiting, so they have minimal impact on agent performance. Failed Slack sends are logged but don't halt execution.

### Q: Can I customize the message format?

**A:** Yes! You can modify the formatter functions in `windows_use/slack/formatter.py` or create your own custom formatters.

## Support

For issues or questions:
- GitHub Issues: [Windows-Use Repository](https://github.com/CursorTouch/Windows-Use/issues)
- Discord: [Join Discord Server](https://discord.com/invite/Aue9Yj2VzS)
- Email: jeogeoalukka@gmail.com

## Contributing

Contributions to improve Slack integration are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

The Slack integration is part of Windows-Use and is licensed under the MIT License. See [LICENSE](LICENSE) for details.
