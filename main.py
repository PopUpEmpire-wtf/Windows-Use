from windows_use.llms.google import ChatGoogle
from windows_use.llms.anthropic import ChatAnthropic
from windows_use.llms.ollama import ChatOllama
from windows_use.llms.mistral import ChatMistral
from windows_use.llms.azure_openai import ChatAzureOpenAI
from windows_use.llms.open_router import ChatOpenRouter
from windows_use.agent import Agent, Browser
from dotenv import load_dotenv
import os

load_dotenv()

# Slack Integration Configuration (Optional)
# ==========================================
# To enable Slack notifications, set the following environment variables in your .env file:
#
# SLACK_NOTIFICATIONS_ENABLED=true
# SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
# # OR use Slack Bot Token instead of webhook:
# # SLACK_BOT_TOKEN=xoxb-your-bot-token
# SLACK_CHANNEL=#windows-use-agent
#
# You can also configure notification preferences:
# - NOTIFY_AGENT_START: Send notification when agent starts (default: true)
# - NOTIFY_AGENT_COMPLETE: Send notification when agent completes (default: true)
# - NOTIFY_TOOL_EXECUTION: Send notification for each tool execution (default: true)
# - NOTIFY_UI_EVENTS: Send notification for UI events (focus/property changes) (default: false)
# - NOTIFY_ERRORS: Send notification for errors (default: true)
#
# The agent will automatically send rich formatted messages to Slack including:
# - Agent start with query, model, and max steps
# - Each step with thought and action
# - Tool executions with parameters and results
# - Completion status with final answer
# - Error notifications with context
#
# The LLM can also send custom messages to Slack using the Slack Tool:
# Example: slack_tool(message="Task completed successfully", color="success")

def main():
    api_key = os.getenv("OPENROUTER_API_KEY")
    # llm=ChatMistral(model='magistral-small-latest',api_key=api_key,temperature=0.7)
    # llm=ChatGoogle(model="gemini-2.5-flash-lite",thinking_budget=0, api_key=api_key, temperature=0.7)
    llm=ChatOpenRouter(model="xiaomi/mimo-v2-flash:free",api_key=api_key,temperature=0.2)
    # llm=ChatAnthropic(model="claude-sonnet-4-5", api_key=api_key, temperature=0.7,max_tokens=1000)
    # llm=ChatOllama(model="qwen3-vl:235b-cloud",temperature=0.2)
    # llm=ChatAzureOpenAI(
    #     endpoint=os.getenv("AOAI_ENDPOINT"),
    #     deployment_name=os.getenv("AOAI_DEPLOYMENT_NAME"),
    #     api_key=os.getenv("AOAI_API_KEY"),
    #     model=os.getenv("AOAI_MODEL"),
    #     api_version=os.getenv("AOAI_API_VERSION", "2025-01-01-preview"),
    #     temperature=0.7
    # )
    agent = Agent(llm=llm, browser=Browser.EDGE, use_vision=False,use_annotation=False, auto_minimize=False)
    agent.print_response(query=input("Enter a query: "))

if __name__ == "__main__":
    main()