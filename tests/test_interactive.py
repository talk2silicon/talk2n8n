"""
Interactive test script for the n8n AI Agent.
"""
import os
import sys
import logging
import asyncio
from dotenv import load_dotenv

# Ensure parent directory is in path for relative imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from agent.agent import Agent
from n8n.tool_registry import ToolRegistry
from n8n.client import N8nClient
from n8n.workflow_converter import WorkflowConverter

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

async def test_workflow_fetch():
    """Test fetching workflows from n8n."""
    logger.info("Testing workflow fetch")
    n8n_client = N8nClient()
    workflows = n8n_client.get_workflows()
    
    if not workflows:
        logger.info("No workflows found in n8n")
        print("No workflows found in n8n")
        return
    
    logger.info(f"Found {len(workflows)} workflows")
    print(f"Found {len(workflows)} workflows:")
    for workflow in workflows:
        logger.info(f"Workflow: {workflow.get('name')} (ID: {workflow.get('id')})")
        print(f"- {workflow.get('name')} (ID: {workflow.get('id')})")

async def test_tool_conversion():
    """Test converting workflows to tools using the Python-based converter."""
    logger.info("Testing tool conversion with Python-based converter")
    n8n_client = N8nClient()
    workflow_converter = WorkflowConverter(n8n_client.base_url)
    
    workflows = n8n_client.get_workflows()
    if not workflows:
        logger.info("No workflows found in n8n")
        print("No workflows found in n8n")
        return
    
    logger.info(f"Converting {len(workflows)} workflows to tools")
    print(f"Converting {len(workflows)} workflows to tools:")
    for workflow in workflows:
        tool = workflow_converter.convert_workflow_to_tool(workflow)
        if tool:
            logger.info(f"Tool: {tool.get('name')} ({len(tool.get('parameters', []))} parameters)")
            logger.info(f"Webhook URL: {tool.get('webhook_url')}")
            logger.info(f"Description: {tool.get('description')}")
            logger.info(f"Parameters: {tool.get('parameters')}")
            print(f"- {tool.get('name')} ({len(tool.get('parameters', []))} parameters)")
            print(f"  Webhook URL: {tool.get('webhook_url')}")
            print(f"  Description: {tool.get('description')}")
            print(f"  Parameters: {tool.get('parameters')}")
            print()
        else:
            logger.info(f"Failed to convert workflow {workflow.get('name')}")
            print(f"- Failed to convert workflow {workflow.get('name')}")

async def test_llm_tool_conversion():
    """Test converting workflows to tools using the LLM-powered converter."""
    logger.info("Testing LLM-powered workflow-to-tool conversion")
    n8n_client = N8nClient()
    workflow_converter = WorkflowConverter(n8n_client.base_url)
    
    # Create a tool registry with debug logging enabled
    tool_registry = ToolRegistry(n8n_client, workflow_converter)
    
    # Fetch workflows from n8n
    workflows = n8n_client.get_workflows()
    if not workflows:
        logger.info("No workflows found in n8n")
        print("No workflows found in n8n")
        return
    
    logger.info(f"Found {len(workflows)} workflows. Submitting to LLM for conversion...")
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
            logger.warning("No workflows found in n8n")
            return
        
        # Load the LangGraph tool schema
        schema_content = tool_registry._load_langgraph_schema()
        logger.info(f"Loaded LangGraph schema, {len(schema_content)} bytes")
        
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
        logger.info("Submitting workflows to Claude for LangGraph tool conversion...")
        llm_response = llm_client.generate_response(prompt, tools=[])
        
        # Store the raw response for inspection
        llm_responses.append(llm_response.get("content", ""))
        logger.info("Claude LLM responded with conversion result")
        logger.debug(f"Raw LLM response:\n{llm_responses[-1]}")
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
                
            logger.info(f"Successfully parsed {len(tools)} tools from Claude's response")
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
                logger.info(f"Converted tool: {json.dumps(tool_def, indent=2)}")
            logger.info(f"Loaded {len(tool_registry.tools)} tools from Claude LLM LangGraph tool conversion")
        except Exception as e:
            logger.error(f"Failed to parse LangGraph tools from Claude response: {e}")
            logger.error(f"Response content: {llm_response.get('content', '')}")
            print(f"Error parsing LLM response: {e}")
            print("Falling back to traditional workflow conversion...")
            tool_registry._fallback_refresh_tools(workflows)
    tool_registry.refresh_tools = patched_refresh
    tool_registry.refresh_tools()
    tool_registry.refresh_tools = original_refresh
    tools = tool_registry.get_tools()
    logger.info(f"Final tool count: {len(tools)}")
    print(f"\nFinal tool count: {len(tools)}")
    for tool in tools:
        print(f"- {tool.get('name')}: {tool.get('description')}")
        print(f"  Parameters: {[p.get('name') for p in tool.get('parameters', [])]}")
        print()
        logger.info(f"Final tool: {tool}")


async def test_interactive_agent():
    """Test the agent interactively."""
    logger.info("Initializing agent for testing")
    # Initialize components
    n8n_client = N8nClient()
    workflow_converter = WorkflowConverter(n8n_client.base_url)
    tool_registry = ToolRegistry(n8n_client, workflow_converter)
    
    # Create the LangGraph-based agent
    agent = Agent(tool_registry)
    
    # Refresh tools
    #tool_registry.refresh_tools()
    tools = tool_registry.get_tools()
    
    logger.info(f"Available tools ({len(tools)}):") 
    print(f"Available tools ({len(tools)}):")    
    for tool in tools:
        logger.info(f"Tool: {tool.get('name')}: {tool.get('description')}")
        print(f"- {tool.get('name')}: {tool.get('description')}")
    
    print("\nEnter 'quit' to exit")
    print("Enter 'refresh' to refresh tools from n8n")
    
    while True:
        try:
            # Get user input
            user_input = input("\nEnter your message: ")
            if user_input.lower() == "quit":
                logger.info("Test completed")
                break
            elif user_input.lower() == "refresh":
                logger.info("Refreshing tools from n8n")
                refresh_result = agent.refresh_tools()
                print(f"\n{refresh_result}")
                
                # Display updated tools
                tools = tool_registry.get_tools()
                print(f"\nAvailable tools ({len(tools)}):")    
                for tool in tools:
                    print(f"- {tool.get('name')}: {tool.get('description')}")
                continue
            
            logger.info(f"User input: {user_input}")
            # Process the message with the LangGraph agent
            logger.info("Processing message...")
            response = agent.process_message(user_input)
            logger.info(f"Agent response: {response}")
            print(f"\nAgent response: {response}")
            
        except KeyboardInterrupt:
            logger.info("Test interrupted by user")
            break
        except Exception as e:
            logger.error(f"Test error: {e}", exc_info=True)
            print(f"Error: {e}")

async def main():
    """Main function."""
    logger.info("Starting interactive test script")
    print("n8n AI Agent Interactive Test")
    print("============================")
    print("Running in interactive mode only")
    
    # Directly run the interactive agent test
    await test_interactive_agent()

if __name__ == "__main__":
    asyncio.run(main())
