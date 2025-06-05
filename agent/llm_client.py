"""
LLM client for generating responses with Claude.
"""
import os
import logging
import json
import re
from typing import Dict, Any, List, Optional
from langchain_anthropic import ChatAnthropic

logger = logging.getLogger(__name__)

class LLMClient:
    """Client for interacting with Claude API."""
    
    def __init__(self, api_key=None, model=None):
        """
        Initialize the LLM client.
        
        Args:
            api_key: API key for Claude (default: from env)
            model: Model to use (default: from env)
        """
        self.api_key = api_key or os.getenv("CLAUDE_API_KEY")
        self.model = model or os.getenv("CLAUDE_MODEL", "claude-3-opus-20240229")
        
        if not self.api_key:
            logger.warning("CLAUDE_API_KEY not set. LLM calls will fail.")
        else:
            self.llm = ChatAnthropic(api_key=self.api_key, model_name=self.model)
    
    def generate_response(self, message: str, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a response from the LLM with tool selection.
        
        Args:
            message: User message
            tools: Available tools
            
        Returns:
            Response with content and/or tool calls
        """
        try:
            # Format tools for Claude
            claude_tools = self._format_tools_for_claude(tools)
            
            # Create system prompt
            system_prompt = """You are an AI assistant that helps users interact with n8n workflows.
            You have access to tools that can trigger these workflows.
            When a user asks you to perform a task, select the most appropriate tool and provide the necessary parameters.
            If no tool matches the user's request, respond conversationally and explain what you can help with.
            """
            
            # Use LangChain's ChatAnthropic for LLM response
            # Note: LangChain's invoke() does not support tool selection in the same way as Claude SDK, so we pass a formatted prompt
            prompt = system_prompt + "\nUser: " + message
            response = self.llm.invoke(prompt)
            return {"content": response.content if hasattr(response, 'content') else str(response)}
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {"content": f"Error generating response: {str(e)}"}
    
    def _format_tools_for_claude(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # This function is now a no-op for LangChain LLM use, but kept for interface compatibility
        return tools
    
    def _process_response(self, response: Any) -> Dict[str, Any]:
        # This function is now a no-op for LangChain LLM use, but kept for interface compatibility
        return {"content": str(response)}
        
    def convert_workflow_to_tool(self, workflow: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert an n8n workflow to a tool definition using the LLM.
        
        Args:
            workflow: The n8n workflow data
            
        Returns:
            Tool definition dictionary or None if conversion failed
        """
        try:
            # Extract webhook node information if available
            webhook_node = None
            webhook_path = None
            code_nodes = []
            
            for node in workflow.get('nodes', []):
                if node.get('type') == 'n8n-nodes-base.webhook':
                    webhook_node = node
                    webhook_path = node.get('parameters', {}).get('path', '')
                elif node.get('type') == 'n8n-nodes-base.code':
                    code_nodes.append(node)
            
            # Prepare a more specific system prompt with examples
            system_prompt = """You are an expert at interpreting n8n workflows and converting them to tool definitions.
            
            Analyze the n8n workflow to create a tool definition that can be used by an AI agent.
            
            IMPORTANT REQUIREMENTS:
            1. The tool definition MUST be valid JSON with these fields: name, description, path, input_schema
            2. Extract parameter names and types from Code nodes that process input data
            3. Only mark parameters as required if they are used without fallback values in the code
            4. The 'path' field should match the webhook node's path parameter
            5. The 'name' should be descriptive and related to the workflow's purpose
            6. DO NOT add any parameters that are not explicitly used in the code nodes
            7. If a parameter has a default value (e.g., 'Guest' for name), make it optional
            
            EXAMPLE INPUT:
            A workflow with a webhook node (path: "emails") and a code node that processes name and email parameters:
            ```
            const name = payload.name || 'Guest';
            const email = payload.email || '';
            ```
            
            EXAMPLE OUTPUT:
            {
              "name": "send_email",
              "description": "Send an email to a recipient",
              "path": "emails",
              "input_schema": {
                "type": "object",
                "properties": {
                  "name": {
                    "type": "string",
                    "description": "Name of the recipient (optional, defaults to 'Guest')"
                  },
                  "email": {
                    "type": "string",
                    "description": "Email address of the recipient"
                  }
                },
                "required": ["email"]
              }
            }
            
            RESPOND ONLY WITH THE JSON TOOL DEFINITION AND NOTHING ELSE.
            """
            
            # Add hints about the webhook and code nodes if available
            hints = []
            if webhook_path:
                hints.append(f"The webhook path is '{webhook_path}'")
            
            # Extract potential parameters from code nodes
            code_params = {}
            for node in code_nodes:
                code = node.get('parameters', {}).get('jsCode', '')
                if code:
                    # Look for patterns like payload.name, items[0].json.email, etc.
                    param_matches = re.findall(r'(?:payload|json)\.(\w+)', code)
                    for param in set(param_matches):
                        # Check if parameter has a default value in the code
                        default_match = re.search(fr'{param}\s*\|\|\s*([\'\"][^\'\"]*[\'\"]|\w+)', code)
                        has_default = default_match is not None
                        code_params[param] = {
                            'has_default': has_default,
                            'default_value': default_match.group(1) if has_default else None
                        }
            
            if code_params:
                params_list = []
                for param, info in code_params.items():
                    default_hint = f" (has default: {info['default_value']})" if info['has_default'] else ""
                    params_list.append(f"- {param}{default_hint}")
                hints.append(f"Parameters found in code:\n" + "\n".join(params_list))
            
            if hints:
                system_prompt += "\n\nHINTS:\n" + "\n".join(hints)
            
            # Prepare the user message with the workflow data
            user_message = f"Convert this n8n workflow to a tool definition:\n\nWorkflow Data:\n{json.dumps(workflow, indent=2)}"
            
            # Get the response from the LLM
            response = self.llm.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ])
            
            # Extract the content from the response
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Try to extract JSON from the response
            try:
                # Look for JSON in the response using a more robust approach
                # First try to parse the entire content as JSON
                try:
                    tool_def = json.loads(content)
                except json.JSONDecodeError:
                    # If that fails, look for JSON object markers
                    json_start = content.find('{')
                    json_end = content.rfind('}')
                    
                    if json_start >= 0 and json_end > json_start:
                        json_str = content[json_start:json_end+1]
                        tool_def = json.loads(json_str)
                    else:
                        logger.warning("No valid JSON found in LLM response")
                        return None
                
                # Ensure required fields are present
                required_fields = ['name', 'description', 'path', 'input_schema']
                missing_fields = [field for field in required_fields if field not in tool_def]
                
                if missing_fields:
                    logger.warning(f"LLM response missing required fields: {', '.join(missing_fields)}")
                    return None
                
                # Ensure input_schema is an object with properties
                if not isinstance(tool_def.get('input_schema', {}), dict) or 'properties' not in tool_def.get('input_schema', {}):
                    logger.warning("input_schema is not properly formatted")
                    return None
                
                return tool_def
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from LLM response: {e}")
                logger.debug(f"Raw LLM response: {content}")
                return None
                
        except Exception as e:
            logger.error(f"Error in convert_workflow_to_tool: {e}")
            return None
