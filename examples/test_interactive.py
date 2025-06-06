"""
Interactive test script for the n8n AI Agent.
"""
import os
import sys
import logging
import asyncio
import pytest
from dotenv import load_dotenv

# Ensure parent directory is in path for relative imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from agent.agent import Agent
from n8n.tool_registry import ToolRegistry
from n8n.client import N8nClient

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_debug.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

@pytest.mark.asyncio
async def test_workflow_fetch():
    """Test fetching workflows from n8n."""
    n8n_client = N8nClient()
    workflows = n8n_client.get_workflows()
    
    if not workflows:
        print("No workflows found in n8n")
        return
    
    print(f"Found {len(workflows)} workflows:")
    for workflow in workflows:
        print(f"- {workflow.get('name')} (ID: {workflow.get('id')})")

# Removed test_tool_conversion function as it relied on WorkflowConverter

@pytest.mark.asyncio
async def test_llm_tool_conversion():
    """Test converting workflows to tools using the LLM-powered converter."""
    n8n_client = N8nClient()
    
    # Create a tool registry
    tool_registry = ToolRegistry(n8n_client)
    
    # Fetch workflows from n8n
    workflows = n8n_client.get_workflows()
    if not workflows:
        print("No workflows found in n8n")
        return
    
    print(f"Found {len(workflows)} workflows. Submitting to LLM for conversion...")
    
    # Patch the tool_registry to capture LLM response
    original_refresh = tool_registry.refresh_tools
    llm_responses = []
    
    def patched_refresh():
        from agent.llm_client import LLMClient
        import json
        import yaml
        
        # Fetch workflows from n8n
        workflows = tool_registry.n8n_client.get_workflows()
        if not workflows:
            return
        
        # Load the LangGraph tool schema
        schema_content = tool_registry._load_langgraph_schema()
        # Schema loaded
        
        # Prepare prompt for Claude
        prompt = (
            "Convert the following n8n workflows directly to LangGraph/LangChain tool format. "
            "For each workflow, extract all webhook and action nodes as separate tools if relevant. "
            "\n\nHere is the LangGraph tool schema format to follow:\n\n"
            f"{schema_content}\n\n"
            "Using this schema as a reference, convert the following n8n workflows to LangGraph tool format. "
            "Make sure each tool has a name, description, parameters with types and descriptions, "
            "and a function section with the webhook_url from the workflow. "
            "Output your response as a valid YAML document that can be parsed.\n\n"
            "Here are the workflows to convert:\n" + json.dumps(workflows, indent=2)
        )
        
        # Create LLM client and submit prompt
        llm_client = LLMClient()
        # Submit to LLM
        llm_response = llm_client.generate_response(prompt, tools=[])
        
        # Store the raw response for inspection
        llm_responses.append(llm_response.get("content", ""))
        # LLM responded
        print(f"\nLLM Response:\n{'-'*50}")
        print(llm_responses[-1][:500] + "..." if len(llm_responses[-1]) > 500 else llm_responses[-1])
        print(f"{'-'*50}\n")
        
        # Continue with normal processing
        try:
            # Try to extract YAML content
            content = llm_response.get("content", "")
            yaml_content = content
            
            # Extract YAML from code blocks if present
            if "```yaml" in content or "```yml" in content:
                import re
                yaml_blocks = re.findall(r'```(?:yaml|yml)\n([\s\S]*?)\n```', content)
                if yaml_blocks:
                    yaml_content = yaml_blocks[0]
                    print(f"Extracted YAML from code block, {len(yaml_content)} bytes")
            
            # Parse the YAML content
            parsed_yaml = yaml.safe_load(yaml_content)
            
            # Extract tools from the parsed YAML
            tools = []
            if isinstance(parsed_yaml, dict) and "tools" in parsed_yaml:
                tools = parsed_yaml["tools"]
            elif isinstance(parsed_yaml, list):
                tools = parsed_yaml
                
            # Tools parsed
            print(f"Successfully parsed {len(tools)} tools from Claude's response")
            
            # Convert the parsed tools to our internal format
            tool_registry.tools = {}
            for tool in tools:
                if "name" not in tool:
                    continue
                webhook_url = ""
                if "function" in tool and "webhook_url" in tool["function"]:
                    webhook_url = tool["function"]["webhook_url"]
                parameters = []
                if "parameters" in tool:
                    for param in tool["parameters"]:
                        param_dict = {
                            "name": param.get("name", ""),
                            "type": param.get("type", "string"),
                            "required": param.get("required", False),
                            "description": param.get("description", "")
                        }
                        if param.get("type") == "array" and "items" in param:
                            param_dict["items"] = param["items"]
                        parameters.append(param_dict)
                tool_def = {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": parameters,
                    "webhook_url": webhook_url,
                    "auth_key": ""
                }
                tool_registry.tools[tool["name"]] = tool_def
                print(f"- Registered tool: {tool['name']}")
                print(f"  Description: {tool.get('description', '')}")
                print(f"  Webhook URL: {webhook_url}")
                print(f"  Parameters: {len(parameters)}")
            # Tools loaded
        except Exception as e:
            logger.error(f"Failed to parse tools: {e}")
            print(f"Error parsing LLM response: {e}")
            print("Error occurred during LLM tool conversion")
    tool_registry.refresh_tools = patched_refresh
    tool_registry.refresh_tools()
    tool_registry.refresh_tools = original_refresh
    tools = tool_registry.get_tools()
    print(f"\nFinal tool count: {len(tools)}")
    for tool in tools:
        print(f"- {tool.get('name')}: {tool.get('description')}")
        print(f"  Parameters: {[p.get('name') for p in tool.get('parameters', [])]}")
        print()
        # Tool registered


@pytest.mark.asyncio
async def test_interactive_agent():
    """Test the agent interactively."""
    # Initialize agent
    # Initialize components
    n8n_client = N8nClient()
    tool_registry = ToolRegistry(n8n_client)
    
    # Create the LangGraph-based agent
    agent = Agent(tool_registry)
    
    # Refresh tools
    #tool_registry.refresh_tools()
    tools = tool_registry.get_tools()
    
    print(f"Available tools ({len(tools)}):")    
    for tool in tools:
        print(f"- {tool.get('name')}: {tool.get('description')}")
    
    print("\nEnter 'quit' to exit")
    print("Enter 'refresh' to refresh tools from n8n")
    
    while True:
        try:
            # Get user input
            user_input = input("\nEnter your message: ")
            if user_input.lower() == "quit":
                # Test completed
                break
            elif user_input.lower() == "refresh":
                # Refresh tools
                refresh_result = agent.refresh_tools()
                print(f"\n{refresh_result}")
                
                # Display updated tools
                tools = tool_registry.get_tools()
                print(f"\nAvailable tools ({len(tools)}):")    
                for tool in tools:
                    print(f"- {tool.get('name')}: {tool.get('description')}")
                continue
            
            logger.info(f"User input: {user_input}")
            # Process message with the LangGraph agent
            logger.info("Processing message...")
            response = agent.process_message(user_input)
            logger.info(f"Agent response: {response}")
            
        except KeyboardInterrupt:
            # Test interrupted
            break
        except Exception as e:
            logger.error(f"Test error: {e}", exc_info=True)
            print(f"Error: {e}")

async def main():
    """Main function."""
    # Start test script
    print("n8n AI Agent Interactive Test")
    print("============================")
    print("Running in interactive mode only")
    
    # Directly run the interactive agent test
    await test_interactive_agent()

if __name__ == "__main__":
    asyncio.run(main())
