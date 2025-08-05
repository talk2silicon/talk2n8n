"""Registry for n8n workflow tools with direct LLM-powered workflow conversion."""

import json
import logging
import os
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin

from langchain.schema import HumanMessage, SystemMessage
from .client import N8nClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert at interpreting n8n workflows and converting them to tool definitions.

For the given workflow, analyze the nodes and connections to understand the workflow's purpose and parameters.

Return the response in JSON format with this exact structure:
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
}

Guidelines:
1. name: Use snake_case, derived from webhook path or workflow purpose
2. description: Clear, concise explanation of what the workflow does
3. method: Always "POST" for n8n webhooks
4. path: Use the webhook node's path
5. input_schema: Analyze code nodes to understand required parameters
"""


class ToolServiceError(Exception):
    """Base exception for tool service errors"""

    pass


class ToolNotFoundError(ToolServiceError):
    """Tool not found"""

    pass


class ToolExecutionError(ToolServiceError):
    """Error executing tool"""

    pass


class ToolService:
    """Service for managing n8n workflow tools with LLM-powered conversion."""

    def __init__(self, n8n_client: N8nClient, llm=None):
        """Initialize the tool service.

        Args:
            n8n_client: N8nClient instance for workflow operations
            llm: Optional LLM instance from Agent for workflow analysis
        """
        self.n8n_client = n8n_client
        self.llm = llm
        self.tools = {}
        self._base_url = os.getenv("N8N_WEBHOOK_BASE_URL", "").rstrip("/")
        self._env = os.getenv("N8N_ENV", "test").lower()

    def sync_workflows(self) -> List[Dict[str, Any]]:
        """Download and convert all active workflows to tools using LLM."""
        logger.info("Syncing workflows to tools using LLM")
        self.tools = {}  # Clear existing tools

        try:
            workflows = self.n8n_client.get_workflows()
            for workflow in workflows:
                logger.info(f"Workflow JSON before conversion: {json.dumps(workflow, indent=2)}")
                if tool := self._convert_workflow_to_tool(workflow):
                    # Add webhook URL
                    prefix = "webhook-test" if self._env == "test" else "webhook"
                    path = tool["path"].lstrip("/")
                    tool["webhook_url"] = f"{self._base_url}/{prefix}/{path}"

                    # Store tool
                    self.tools[tool["name"]] = tool
                    logger.info(f"Registered tool: {tool['name']} -> {tool['webhook_url']}")

            return list(self.tools.values())

        except Exception as e:
            logger.error(f"Error syncing workflows: {e}")
            raise ToolServiceError(f"Failed to sync workflows: {e}")

    def get_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get a tool by name.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool definition if found, None otherwise

        Raises:
            ToolNotFoundError: If tool not found
        """
        tool = self.tools.get(tool_name)
        if not tool:
            raise ToolNotFoundError(f"Tool '{tool_name}' not found")
        return tool

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools.

        Returns:
            List of tool definitions
        """
        return list(self.tools.values())

    def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with parameters.

        Args:
            tool_name: Name of tool to execute
            params: Tool parameters

        Returns:
            Tool execution result

        Raises:
            ToolNotFoundError: If tool not found
            ToolExecutionError: If execution fails
        """
        try:
            # Get tool definition
            tool = self.get_tool(tool_name)
            if not tool:
                raise ToolNotFoundError(f"Tool '{tool_name}' not found")
            logger.info(f"Calling tool '{tool_name}' with params: {json.dumps(params, indent=2)}")
            # Get webhook URL
            webhook_url = tool["webhook_url"]
            if not webhook_url:
                raise ToolExecutionError(f"No webhook URL for tool '{tool_name}'")
            # Make HTTP request
            response = self.n8n_client.trigger_webhook(webhook_url, params)
            logger.info(f"Tool execution completed: {tool_name}")
            return response
        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {e}")
            return {"status": "error", "message": str(e), "tool": tool_name}

    def _convert_workflow_to_tool(self, workflow: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert workflow to tool using LLM analysis.

        Args:
            workflow: n8n workflow data

        Returns:
            Tool definition if conversion successful, None otherwise
        """
        if not self.llm:
            logger.error("No LLM instance available for workflow conversion")
            return None

        try:
            # Prepare messages for LLM
            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(
                    content=f"Here is the workflow to analyze:\n{json.dumps(workflow, indent=2)}"
                ),
            ]

            # Get LLM response
            response = self.llm.invoke(messages)
            logger.info(f"LLM output for workflow '{workflow.get('name', '')}': {response.content}")
            # Parse response
            try:
                tool_def = json.loads(response.content)
                logger.info(
                    f"Successfully converted workflow {workflow.get('name')} to tool {tool_def.get('name')}"
                )
                return tool_def
            except json.JSONDecodeError:
                logger.error("Failed to parse LLM response as JSON")
                return None

        except Exception as e:
            logger.error(f"Error in LLM conversion: {e}")
            return None
