"""
LLM-based workflow analyzer for n8n workflows.
"""
import json
import logging
from typing import Dict, Any, List, Optional

from anthropic import Anthropic

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert at interpreting n8n workflows and converting them to tool definitions.

For the given workflow, analyze the nodes and connections to understand the workflow's purpose and parameters.

For each webhook node, provide:
1. A clear, descriptive name (use the webhook path if available)
2. A concise description of what the workflow does
3. The required input parameters with their types and descriptions
4. Any important notes about how to use the tool

Focus on the business logic and required inputs. Ignore UI-specific configurations.

Return the response in JSON format with this structure:
{
  "name": "tool_name_based_on_path",
  "description": "What the workflow does",
  "method": "HTTP_METHOD",
  "path": "webhook_path",
  "parameters": [
    {
      "name": "param1",
      "type": "string",
      "description": "What this parameter is used for",
      "required": true
    }
  ]
}"""

class WorkflowAnalyzer:
    """Analyzes n8n workflows using LLM to extract tool definitions."""
    
    def __init__(self):
        """Initialize the workflow analyzer with an LLM client."""
        self.llm = Anthropic()
    
    def analyze_workflow(self, workflow: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze a workflow and return tool definitions.
        
        Args:
            workflow: The n8n workflow data
            
        Returns:
            List of tool definitions
        """
        if not isinstance(workflow, dict) or 'nodes' not in workflow:
            return []
            
        # Find all webhook nodes
        webhook_nodes = [
            node for node in workflow.get('nodes', [])
            if node.get('type') == 'n8n-nodes-base.webhook'
        ]
        
        if not webhook_nodes:
            return []
            
        tools = []
        for webhook_node in webhook_nodes:
            try:
                tool = self._analyze_webhook_node(webhook_node, workflow)
                if tool:
                    tools.append(tool)
            except Exception as e:
                logger.error(f"Error analyzing webhook node {webhook_node.get('id')}: {e}")
                
        return tools
    
    def _analyze_webhook_node(self, webhook_node: Dict[str, Any], workflow: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze a single webhook node and return its tool definition."""
        path = webhook_node.get('parameters', {}).get('path', '').strip('/')
        if not path:
            return None
            
        method = webhook_node.get('parameters', {}).get('httpMethod', 'POST')
        
        # Prepare workflow data for LLM
        workflow_data = {
            'name': workflow.get('name', 'Unnamed Workflow'),
            'webhook_path': path,
            'webhook_method': method,
            'nodes': [
                {
                    'id': node['id'],
                    'type': node['type'],
                    'name': node.get('name', '')
                }
                for node in workflow.get('nodes', [])
            ]
        }
        
        try:
            # Get analysis from LLM
            response = self.llm.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=2000,
                temperature=0.1,
                system=SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Analyze this n8n workflow and extract tool definitions for webhook endpoints.\n\nWorkflow Data:\n{json.dumps(workflow_data, indent=2)}"
                            }
                        ]
                    }
                ]
            )
            
            # Extract the JSON response from the LLM
            content = response.content[0].text
            tool_def = json.loads(content)
            
            # Add method and path to the tool definition
            tool_def['method'] = method
            tool_def['path'] = path
            
            # Convert parameters to the required format
            if 'parameters' in tool_def and isinstance(tool_def['parameters'], list):
                properties = {}
                required = []
                
                for param in tool_def['parameters']:
                    param_name = param.get('name')
                    if not param_name:
                        continue
                        
                    properties[param_name] = {
                        'type': param.get('type', 'string'),
                        'description': param.get('description', '')
                    }
                    
                    if param.get('required', False):
                        required.append(param_name)
                
                tool_def['input_schema'] = {
                    'type': 'object',
                    'properties': properties,
                    'required': required
                }
            
            return tool_def
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            # Fall back to a basic tool definition
            return {
                'name': path.replace('-', '_').lower(),
                'description': f"Triggers the {path} webhook endpoint",
                'method': method,
                'path': path,
                'input_schema': {
                    'type': 'object',
                    'properties': {},
                    'required': []
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing webhook node with LLM: {e}")
            # Fallback to basic tool definition
            return {
                'name': path.replace('/', '_').strip('_'),
                'description': f"Triggers the {path} webhook",
                'method': method,
                'path': path,
                'input_schema': {
                    'type': 'object',
                    'properties': {},
                    'required': []
                }
            }
