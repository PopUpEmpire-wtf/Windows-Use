"""Entry point for Windows-Use Slack integration."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Windows-Use components
from windows_use.slack import SlackAgent


def get_llm():
    """
    Get LLM instance based on environment variables.

    Returns:
        LLMInterface: Configured LLM instance
    """
    # Check for API keys and initialize appropriate LLM
    if os.getenv("ANTHROPIC_API_KEY"):
        from windows_use.llms.anthropic import AnthropicLLM
        return AnthropicLLM(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model="claude-3-5-sonnet-20241022"
        )

    elif os.getenv("OPENAI_API_KEY"):
        from windows_use.llms.openai import OpenAILLM
        return OpenAILLM(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o"
        )

    elif os.getenv("GOOGLE_API_KEY"):
        from windows_use.llms.google import GoogleLLM
        return GoogleLLM(
            api_key=os.getenv("GOOGLE_API_KEY"),
            model="gemini-2.0-flash-exp"
        )

    elif os.getenv("MISTRAL_API_KEY"):
        from windows_use.llms.mistral import MistralLLM
        return MistralLLM(
            api_key=os.getenv("MISTRAL_API_KEY"),
            model="mistral-large-latest"
        )

    elif os.getenv("GROQ_API_KEY"):
        from windows_use.llms.groq import GroqLLM
        return GroqLLM(
            api_key=os.getenv("GROQ_API_KEY"),
            model="llama-3.3-70b-versatile"
        )

    elif os.getenv("OLLAMA_BASE_URL"):
        from windows_use.llms.ollama import OllamaLLM
        return OllamaLLM(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            model="llama3.2"
        )

    else:
        print("❌ Error: No LLM API key found in environment variables.")
        print("\nPlease set one of the following environment variables:")
        print("  - ANTHROPIC_API_KEY (for Claude)")
        print("  - OPENAI_API_KEY (for GPT)")
        print("  - GOOGLE_API_KEY (for Gemini)")
        print("  - MISTRAL_API_KEY (for Mistral)")
        print("  - GROQ_API_KEY (for Groq)")
        print("  - OLLAMA_BASE_URL (for local Ollama)")
        print("\nYou can copy .env.example to .env and add your API keys there.")
        sys.exit(1)


def main():
    """Main entry point for Slack bot."""
    print("🚀 Starting Windows-Use Slack Agent...")

    # Check for required Slack tokens
    if not os.getenv("SLACK_BOT_TOKEN"):
        print("❌ Error: SLACK_BOT_TOKEN not found in environment variables.")
        print("\nPlease set SLACK_BOT_TOKEN in your .env file.")
        print("Get it from: https://api.slack.com/apps -> Your App -> OAuth & Permissions")
        sys.exit(1)

    if not os.getenv("SLACK_APP_TOKEN"):
        print("❌ Error: SLACK_APP_TOKEN not found in environment variables.")
        print("\nPlease set SLACK_APP_TOKEN in your .env file.")
        print("Get it from: https://api.slack.com/apps -> Your App -> Basic Information -> App-Level Tokens")
        print("Make sure Socket Mode is enabled and the token has 'connections:write' scope.")
        sys.exit(1)

    # Initialize LLM
    print("🔧 Initializing LLM...")
    llm = get_llm()
    print(f"✓ Using {llm.__class__.__name__}")

    # Initialize Slack agent
    print("🔧 Initializing Slack agent...")
    slack_agent = SlackAgent(
        llm=llm,
        # Optional agent configuration
        # browser='chrome',  # or 'edge', 'firefox'
        # vision=True,  # Enable vision mode for screenshots
    )

    print("✓ Slack agent initialized")
    print("\n" + "="*50)
    print("🤖 Windows-Use Slack Agent is now running!")
    print("="*50)
    print("\nYou can now:")
    print("  1. Send a DM to the bot")
    print("  2. @mention the bot in a channel")
    print("  3. Use /windows command")
    print("\nPress Ctrl+C to stop the agent.")
    print("="*50 + "\n")

    # Start the agent
    try:
        slack_agent.start()
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping Slack agent...")
        slack_agent.stop()
        print("✓ Agent stopped. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
