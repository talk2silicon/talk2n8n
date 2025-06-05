"""
Main entry point for the n8n AI Agent application.
"""
import os
import logging
from dotenv import load_dotenv

from slack.handler import SlackHandler
from agent.agent import Agent
from agent.llm_client import LLMClient
from n8n.tool_registry import ToolRegistry
from n8n.client import N8nClient
from n8n.workflow_converter import WorkflowConverter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def main():
    """Initialize and start the application."""
    # Initialize n8n client
    n8n_client = N8nClient(
        base_url=os.getenv("N8N_BASE_URL"),
        api_key=os.getenv("N8N_API_KEY")
    )
    
    # Initialize workflow converter
    workflow_converter = WorkflowConverter(n8n_client.base_url)
    
    # Initialize tool registry
    tool_registry = ToolRegistry(n8n_client, workflow_converter)
    
    # Initialize LLM client
    llm_client = LLMClient()
    
    # Initialize agent
    agent = Agent(tool_registry, llm_client)
    
    # Initialize and start Slack handler
    slack_handler = SlackHandler(agent)
    slack_handler.start()

if __name__ == "__main__":
    main()
