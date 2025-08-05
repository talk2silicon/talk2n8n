"""
Factory for creating tool instances from tool definitions.
"""

# Standard library imports
import logging
from typing import Any, Callable, Dict, Optional

# Local application imports
from src.config import settings


# Initialize logger
logger = logging.getLogger(__name__)


class ToolFactory:
    """Creates tool instances from tool definitions."""

    @classmethod
    def create_tool(
        cls,
        tool_def: Dict[str, Any],
        webhook_base_url: Optional[str] = None,
        env: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a tool instance from a tool definition.

        Args:
            tool_def: The tool definition
            webhook_base_url: Base URL for n8n webhooks. Uses config if not provided.
            env: Environment ('test', 'development', 'staging', or 'production'). Uses config if not provided.

        Returns:
            A dictionary representing the tool with additional metadata
        """
        # Use provided values or fall back to config
        webhook_base_url = (webhook_base_url or settings.N8N_WEBHOOK_BASE_URL).rstrip("/")
        env = (env or settings.N8N_ENV).lower()

        try:
            # Add webhook URL to the tool definition
            prefix = "webhook-test" if env == "test" else "webhook"
            path = tool_def["path"].lstrip("/")

            # Create a copy of the tool definition with additional metadata
            tool = tool_def.copy()
            tool["webhook_url"] = f"{webhook_base_url}/{prefix}/{path}"

            # Add execute method if not present
            if "execute" not in tool:
                tool["execute"] = ToolFactory._create_execute_function(tool)

            return tool

        except Exception as e:
            logger.error(f"Error creating tool from definition: {e}", exc_info=True)
            raise

    @staticmethod
    def _create_execute_function(tool_def: Dict[str, Any]) -> Callable:
        """
        Create an execute function for the tool.

        Args:
            tool_def: The tool definition

        Returns:
            A callable function that executes the tool
        """

        def execute(**kwargs):
            # In a real implementation, this would make an HTTP request to the webhook
            # For now, we'll just return the tool definition and input
            return {
                "tool": tool_def["name"],
                "input": kwargs,
                "webhook_url": tool_def.get("webhook_url"),
            }

        return execute

    @classmethod
    def create_tools_from_definitions(
        cls,
        tool_defs: list[Dict[str, Any]],
        webhook_base_url: Optional[str] = None,
        env: Optional[str] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Create multiple tool instances from a list of tool definitions.

        Args:
            tool_defs: List of tool definitions
            webhook_base_url: Base URL for n8n webhooks
            env: Environment ('test' or 'production')

        Returns:
            Dictionary of tool name to tool instance
        """
        tools = {}
        for tool_def in tool_defs:
            try:
                tool = cls.create_tool(tool_def, webhook_base_url, env)
                tools[tool["name"]] = tool
            except Exception as e:
                logger.error(f"Failed to create tool from definition: {e}")
                continue

        return tools
