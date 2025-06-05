"""
Converter for n8n workflows to LLM tools.
"""
import logging
import re
import json
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class WorkflowConverter:
    """Converter for n8n workflows to LLM tools."""
    
    def __init__(self, base_url=None):
        """
        Initialize the workflow converter.
        
        Args:
            base_url: Base URL of the n8n instance
        """
        self.base_url = base_url
    
    def convert_workflow_to_tool(self, workflow: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert an n8n workflow to a tool definition.
        
        Args:
            workflow: n8n workflow data
            
        Returns:
            Tool definition if conversion successful, None otherwise
        """
        logger.info(f"Converting workflow: {workflow.get('name')}")
        logger.debug(f"Raw workflow input:\n{json.dumps(workflow, indent=2)}")
        
        try:
            # Extract basic workflow info
            workflow_id = workflow.get("id")
            workflow_name = workflow.get("name", "Unnamed Workflow")
            
            # Find webhook node
            webhook_node = self._find_webhook_node(workflow)
            if not webhook_node:
                logger.warning(f"No webhook node found in workflow {workflow_id}")
                return None
            
            # Extract webhook path
            webhook_path = webhook_node.get("parameters", {}).get("path")
            if not webhook_path:
                logger.warning(f"No webhook path found in workflow {workflow_id}")
                return None
            
            # Ensure webhook path starts with a slash
            if not webhook_path.startswith("/"):
                webhook_path = f"/{webhook_path}"
            
            # Extract parameters from code nodes
            parameters = self._extract_parameters(workflow)
            
            # Create tool definition
            tool = {
                "name": self._sanitize_name(workflow_name),
                "auth_key": "",
                "parameters": parameters,
                "description": self._generate_description(workflow),
                "webhook_url": webhook_path,
                "original_workflow": workflow  # Keep full original for reference
            }
            
            logger.info(f"Generated tool definition:\n{json.dumps(tool, indent=2)}")
            return tool
            
        except Exception as e:
            logger.error(f"Error converting workflow {workflow.get('id')}: {e}")
            return None
    
    def _find_webhook_node(self, workflow: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find the webhook node in a workflow.
        
        Args:
            workflow: n8n workflow data
            
        Returns:
            Webhook node if found, None otherwise
        """
        for node in workflow.get("nodes", []):
            if node.get("type") == "n8n-nodes-base.webhook":
                return node
        return None
    
    def _extract_parameters(self, workflow: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract parameters from workflow nodes.
        
        Args:
            workflow: n8n workflow data
            
        Returns:
            List of parameter definitions
        """
        logger.debug(f"Extracting parameters from workflow nodes")
        parameters = []
        
        # Look for code nodes that process input
        for node in workflow.get("nodes", []):
            if node.get("type") == "n8n-nodes-base.code":
                code = node.get("parameters", {}).get("jsCode", "")
                params = self._extract_params_from_code(code)
                parameters.extend(params)
        
        # If no parameters found, create a default one based on webhook path
        if not parameters:
            webhook_node = self._find_webhook_node(workflow)
            if webhook_node:
                path = webhook_node.get("parameters", {}).get("path", "")
                param_name = path.strip("/").split("/")[-1]
                if param_name:
                    parameters.append({
                        "name": param_name,
                        "type": "string",
                        "required": True,
                        "description": f"Input for the {path} webhook"
                    })
        
        return parameters
    
    def _extract_params_from_code(self, code: str) -> List[Dict[str, Any]]:
        """
        Extract parameters from JavaScript code.
        
        Args:
            code: JavaScript code from a code node
            
        Returns:
            List of parameter definitions
        """
        params = []
        
        # Look for common patterns in code
        # Pattern 1: items[0].json.body.X
        body_params = re.findall(r'items\[0\]\.json\.body\.(\w+)', code)
        
        for param in body_params:
            # Check if it's an array
            is_array = bool(re.search(rf'{param}\.map\(', code) or 
                           re.search(rf'{param}\.forEach\(', code) or
                           re.search(rf'{param}\[', code))
            
            params.append({
                "name": param,
                "type": "array" if is_array else "string",
                "items": {"type": "string"} if is_array else None,
                "required": True,
                "description": f"Parameter '{param}' extracted from workflow code"
            })
            
            # Remove None values for arrays
            if not is_array:
                params[-1].pop("items")
        
        return params
    
    def _generate_description(self, workflow: Dict[str, Any]) -> str:
        """
        Generate a description for the workflow.
        
        Args:
            workflow: n8n workflow data
            
        Returns:
            Description string
        """
        name = workflow.get("name", "Unnamed Workflow")
        
        # Check if workflow has a description
        if workflow.get("meta", {}) and workflow.get("meta", {}).get("description"):
            return workflow.get("meta", {}).get("description")
        
        # Generate a description based on nodes
        node_types = [node.get("name", "") for node in workflow.get("nodes", [])]
        node_str = ", ".join(filter(None, node_types))
        
        return f"Trigger the '{name}' workflow which uses {node_str}"
    
    def _sanitize_name(self, name: str) -> str:
        """
        Sanitize workflow name for use as a tool name.
        
        Args:
            name: Workflow name
            
        Returns:
            Sanitized name
        """
        # Convert to lowercase
        name = name.lower()
        # Replace spaces with underscores
        name = name.replace(" ", "_")
        # Remove special characters
        name = re.sub(r'[^a-z0-9_]', '', name)
        
        return name
