#!/usr/bin/env python
"""
Simple test script for testing the n8n AI Agent with user prompts.

This script provides an interactive interface to test the n8n AI Agent.
"""
# Standard library imports
import logging
import sys
from pathlib import Path
from typing import Optional

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

# Third-party imports
from langchain_anthropic import ChatAnthropic

# Local application imports
from src.agent.agent import Agent
from src.config.settings import settings


# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Default prompt for quick testing; set to None to disable auto-run
DEFAULT_PROMPT = None

def interactive_mode(agent: Agent) -> None:
    """Run the agent in interactive mode.
    
    Args:
        agent: The agent instance to run
    """
    print("\n=== n8n AI Agent ===")
    print("Type 'exit' to quit, 'refresh' to reload workflows, 'help' for help")

    # Auto-run the default prompt if set
    if DEFAULT_PROMPT:
        print(f"\n[Auto] You: {DEFAULT_PROMPT}")
        response = agent.run(DEFAULT_PROMPT)
        print(f"Agent: {response}")
    
    while True:
        try:
            # Get user input
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() == 'exit':
                print("Goodbye!")
                break
                
            if user_input.lower() == 'refresh':
                print("Refreshing tools from n8n...")
                try:
                    agent.refresh_tools()
                    print("Tools refreshed successfully!")
                except Exception as e:
                    print(f"Failed to refresh tools: {e}")
                continue
                
            if user_input.lower() == 'help':
                print("\nAvailable commands:")
                print("  exit     - Exit the program")
                print("  refresh  - Reload workflows from n8n")
                print("  help     - Show this help message")
                continue
                
            # Process the input
            print("\nProcessing your request...")
            try:
                response = agent.run(user_input)
                # Print the response
                if response:
                    print(f"\nAgent: {response}")
                else:
                    print("No response from agent")
            except Exception as e:
                print(f"Error processing your request: {e}")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            if settings.N8N_ENV == "development":
                import traceback
                traceback.print_exc()

def initialize_llm() -> ChatAnthropic:
    """Initialize the language model.
    
    Returns:
        An instance of ChatAnthropic
    """
    if not settings.CLAUDE_API_KEY:
        raise ValueError("CLAUDE_API_KEY is not set in environment variables")
    
    return ChatAnthropic(
        model=settings.CLAUDE_MODEL,
        temperature=0.0,
        api_key=settings.CLAUDE_API_KEY
    )

def main() -> None:
    """Main function to run the example."""
    logger.info("Starting n8n AI Agent...")
    logger.debug("Environment: %s", settings.N8N_ENV)
    
    try:
        # Initialize the LLM
        llm = initialize_llm()
        logger.info("LLM initialized with model: %s", settings.CLAUDE_MODEL)
        
        # Initialize the agent with the LLM
        agent = Agent(llm=llm)
        logger.info("Agent initialized")
        
        # Start interactive mode
        interactive_mode(agent)
        
    except Exception as e:
        logger.critical("Failed to initialize the agent: %s", e, exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nScript terminated by user")
        sys.exit(0)
    except Exception as e:
        logger.critical("Unhandled exception: %s", e, exc_info=True)
        sys.exit(1)
