"""
Registry for n8n workflow tools with direct LLM-powered workflow conversion.
"""
import json
import logging
import os
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin

# Use absolute import path instead of relative
from agent.llm_client import LLMClient
from .client import N8nClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert at interpreting n8n workflows and converting them to tool definitions.

For the given workflow, analyze the nodes and connections to understand the workflow's purpose and parameters.

For each webhook node, provide a tool definition with:
1. A clear, descriptive name (use the webhook path if available)
2. A concise description of what the workflow does
3. The required input parameters with their types and descriptions

Return the response in JSON format with this structure:
{
  "name": "tool_name_based_on_path",
  "description": "What the workflow does",
  "method": "POST",
  "path": "webhook_path",
  "input_schema": {
    "type": "object",
    "properties": {
      "param1": {
        "type": "string",
        "description": "What this parameter is used for"
      }
    },
    "required": ["param1"]
  }
}"""

class ToolRegistry:
    """Registry for n8n workflow tools with direct LLM conversion."""
    
    def __init__(self, n8n_client: N8nClient = None, workflow_converter = None):
        """
        Initialize the tool registry.
        
        Args:
            n8n_client: Client for interacting with n8n API
            workflow_converter: Optional workflow converter (kept for backward compatibility)
        """
        self.n8n_client = n8n_client or N8nClient()
        self.workflow_converter = workflow_converter
        self.llm_client = LLMClient()
        self.tools = {}
        self._base_url = os.getenv("N8N_WEBHOOK_BASE_URL", "https://n8n-app-young-feather-1595.fly.dev").rstrip('/')
        self._env = os.getenv("N8N_ENV", "test").lower()
    
    def refresh_tools(self) -> None:
        """
        Refresh tools from n8n workflows using direct LLM conversion.
        """
        logger.info("Refreshing tools from n8n workflows using direct LLM conversion...")
        
        # Clear existing tools
        self.tools = {}
        
        # Fetch workflows from n8n
        workflows = self.n8n_client.get_workflows()
        if not workflows:
            logger.warning("No workflows found in n8n")
            return
            
        logger.info(f"Found {len(workflows)} workflows, converting with LLM...")
        
        # Process each workflow
        for workflow in workflows:
            if not isinstance(workflow, dict):
                continue
                
            # Convert workflow to tool definition using LLM
            try:
                tool_def = self._convert_workflow_to_tool(workflow)
                if tool_def:
                    # Add webhook URL to the tool definition
                    prefix = 'webhook-test' if self._env == 'test' else 'webhook'
                    path = tool_def['path'].lstrip('/')
                    tool_def['webhook_url'] = f"{self._base_url}/{prefix}/{path}"
                    
                    # Register the tool
                    self.tools[tool_def['name']] = tool_def
                    logger.info(f"Registered tool: {tool_def['name']} -> {tool_def['webhook_url']}")
            except Exception as e:
                logger.error(f"Error converting workflow {workflow.get('name', 'unknown')}: {e}")
        
        logger.info(f"Successfully registered {len(self.tools)} tools")
        
    def _convert_workflow_to_tool(self, workflow: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert a workflow to a tool definition using the LLMClient's direct conversion method.
        
        Args:
            workflow: The workflow data
            
        Returns:
            Tool definition or None if conversion failed
        """
        try:
            # Use the LLMClient's dedicated method for workflow conversion
            tool_def = self.llm_client.convert_workflow_to_tool(workflow)
            if not tool_def:
                logger.warning(f"LLM response missing required fields for workflow {workflow.get('name', 'unknown')}")
            return tool_def
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return None
            
        except Exception as e:
            logger.error(f"Error in LLM conversion: {e}")
            return None

    
    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Get all registered tools.
        
        Returns:
            List of tool definitions
        """
        return list(self.tools.values())
    
    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a tool by name.
        
        Args:
            name: Name of the tool to get
            
        Returns:
            Tool definition if found, None otherwise
        """
        return self.tools.get(name)
    
    def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool by name.
        
        Args:
            tool_name: Name of the tool to execute
            params: Parameters for the tool
            
        Returns:
            Result of the tool execution
        """
        logger.info(f"Executing tool: {tool_name}")
        logger.debug(f"Tool params: {params}")
        
        tool = self.get_tool(tool_name)
        if not tool:
            error_msg = f"Tool '{tool_name}' not found"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
        
        webhook_url = tool.get("webhook_url")
        if not webhook_url:
            error_msg = f"No webhook URL found for tool '{tool_name}'"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
        
        method = tool.get('method', 'POST')
        
        logger.info(f"Triggering {method} webhook: {webhook_url}")
        logger.debug(f"Webhook payload: {params}")
        
        try:
            # The trigger_webhook method will automatically try both POST and GET methods
            result = self.n8n_client.trigger_webhook(webhook_url, params)
                
            logger.info(f"Tool execution completed for {tool_name}")
            logger.debug(f"Tool result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            return {
                "status": "error", 
                "message": str(e),
                "tool": tool_name,
                "url": webhook_url
            }
