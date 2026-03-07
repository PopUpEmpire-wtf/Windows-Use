"""Entry point for the Windows-Use ClickUp integration."""

import os
import sys

from dotenv import load_dotenv

# Load environment variables from .env file.
load_dotenv()

from windows_use.clickup import ClickUpAgent  # noqa: E402


def get_llm():
    """
    Build an LLM instance from environment variables.

    Checks for API keys in the following order: Anthropic, OpenAI, Google,
    Mistral, Groq, Ollama.

    Returns:
        A configured LLM instance conforming to ``BaseChatLLM``.
    """
    if os.getenv("ANTHROPIC_API_KEY"):
        from windows_use.llms.anthropic import ChatAnthropic

        return ChatAnthropic(
            model="claude-sonnet-4-5",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        )

    if os.getenv("OPENAI_API_KEY"):
        from windows_use.llms.openai import ChatOpenAI

        return ChatOpenAI(
            model="gpt-4o",
            api_key=os.getenv("OPENAI_API_KEY"),
        )

    if os.getenv("GOOGLE_API_KEY"):
        from windows_use.llms.google import ChatGoogle

        return ChatGoogle(
            model="gemini-2.5-flash",
            api_key=os.getenv("GOOGLE_API_KEY"),
        )

    if os.getenv("MISTRAL_API_KEY"):
        from windows_use.llms.mistral import ChatMistral

        return ChatMistral(
            model="mistral-large-latest",
            api_key=os.getenv("MISTRAL_API_KEY"),
        )

    if os.getenv("GROQ_API_KEY"):
        from windows_use.llms.groq import ChatGroq

        return ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=os.getenv("GROQ_API_KEY"),
        )

    if os.getenv("OLLAMA_BASE_URL"):
        from windows_use.llms.ollama import ChatOllama

        return ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "llama3.2"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        )

    print("❌ Error: No LLM API key found in environment variables.")
    print("\nPlease set one of the following in your .env file:")
    print("  ANTHROPIC_API_KEY  — Claude")
    print("  OPENAI_API_KEY     — GPT")
    print("  GOOGLE_API_KEY     — Gemini")
    print("  MISTRAL_API_KEY    — Mistral")
    print("  GROQ_API_KEY       — Groq")
    print("  OLLAMA_BASE_URL    — local Ollama")
    sys.exit(1)


def main():
    """Main entry point for the ClickUp bot."""
    print("🚀 Starting Windows-Use ClickUp Agent...")

    if not os.getenv("CLICKUP_API_KEY"):
        print("❌ Error: CLICKUP_API_KEY not found in environment variables.")
        print("\nPlease set CLICKUP_API_KEY in your .env file.")
        print("Get it from: https://app.clickup.com/settings/apps")
        sys.exit(1)

    host = os.getenv("CLICKUP_WEBHOOK_HOST", "0.0.0.0")
    port = int(os.getenv("CLICKUP_WEBHOOK_PORT", "8000"))
    task_tag = os.getenv("CLICKUP_TASK_TAG", "windows-agent")
    bot_name = os.getenv("CLICKUP_BOT_NAME", "windows-agent")

    print("🔧 Initializing LLM...")
    llm = get_llm()
    print(f"✓ Using {llm.__class__.__name__}")

    print("🔧 Initializing ClickUp agent...")
    clickup_agent = ClickUpAgent(
        llm=llm,
        task_tag=task_tag,
        bot_name=bot_name,
    )
    print("✓ ClickUp agent initialized")

    print("\n" + "=" * 50)
    print("🤖 Windows-Use ClickUp Agent is running!")
    print("=" * 50)
    print(f"\nWebhook URL: http://<your-server>:{port}/webhook")
    print(f"Health check: http://<your-server>:{port}/health")
    print(f"Task tag:  {task_tag}")
    print(f"Bot name:  @{bot_name}")
    print("\nRegister the webhook URL in ClickUp:")
    print("  Settings → Integrations → Webhooks → + New Webhook")
    print("\nPress Ctrl+C to stop.")
    print("=" * 50 + "\n")

    try:
        clickup_agent.start(host=host, port=port)
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping ClickUp agent... Goodbye!")


if __name__ == "__main__":
    main()
