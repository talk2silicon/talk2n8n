# n8n Workflow Integration Design

## Overview

This document outlines the design for integrating n8n workflows with an LLM-powered agent. The system automatically converts n8n workflows to LLM tools without manual processing, enabling natural language interaction with n8n workflows. The implementation directly uses the Anthropic API with proper tool schema formatting for Claude.

## Key Features

- **Automatic Workflow Conversion**: Converts n8n workflows to LLM tools by analyzing webhook and code nodes
- **Dynamic Parameter Extraction**: Automatically extracts required parameters from workflow code
- **Flexible Webhook Handling**: Supports both POST and GET methods with automatic fallback
- **Environment-Based Configuration**: Uses environment variables for webhook URLs and API keys
- **Robust Error Handling**: Provides detailed error messages and logging

## Core Components

### 1. N8nClient
Responsible for communicating with the n8n API to fetch workflows and trigger webhooks.

```python
class N8nClient:
    def __init__(self, base_url=None, api_key=None):
        self.base_url = base_url or os.getenv("N8N_BASE_URL")
        self.api_key = api_key or os.getenv("N8N_API_KEY")
        
    def get_workflows(self) -> List[Dict]:
        """Fetch all workflows from n8n API"""
        headers = {"X-N8N-API-KEY": self.api_key, "Accept": "application/json"}
        response = requests.get(f"{self.base_url}/api/v1/workflows", headers=headers)
        response.raise_for_status()
        return response.json().get("data", [])
        
    def trigger_webhook(self, webhook_url: str, payload: Dict) -> Dict:
        """
        Trigger a webhook with the given payload. Tries both POST and GET methods.
        
        Args:
            webhook_url: URL of the webhook to trigger
            payload: Payload to send to the webhook
            
        Returns:
            Response from the webhook
        """
        # If webhook_url is relative, make it absolute
        if not webhook_url.startswith("http"):
            webhook_url = f"{self.base_url}{webhook_url if webhook_url.startswith('/') else '/' + webhook_url}"
        
        # First try POST method
        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            # If POST fails, try GET with params
            response = requests.get(webhook_url, params=payload, timeout=10)
            response.raise_for_status()
            
        return response.json() if response.text else {}
```

### 2. LLMClient
Handles the conversion of n8n workflows to tool definitions using Claude.

```python
class LLMClient:
    def convert_workflow_to_tool(self, workflow: Dict) -> Optional[Dict]:
        """
        Convert an n8n workflow to a tool definition using the LLM.
        
        Args:
            workflow: The n8n workflow data
            
        Returns:
            Tool definition dictionary or None if conversion failed
        """
        # Extract webhook and code node information
        webhook_node = next((n for n in workflow.get('nodes', []) 
                           if n.get('type') == 'n8n-nodes-base.webhook'), None)
        code_nodes = [n for n in workflow.get('nodes', []) 
                     if n.get('type') == 'n8n-nodes-base.code']
        
        # Analyze code nodes to extract parameters and their default values
        code_params = {}
        for node in code_nodes:
            code = node.get('parameters', {}).get('jsCode', '')
            if code:
                param_matches = re.findall(r'(?:payload|json)\.(\\w+)', code)
                for param in set(param_matches):
                    default_match = re.search(fr'{param}\\s*\\|\\|\\s*([\\'\\\"][^\\'\\\"]*[\\'\\\"]|\\w+)', code)
                    has_default = default_match is not None
                    code_params[param] = {
                        'has_default': has_default,
                        'default_value': default_match.group(1) if has_default else None
                    }
        
        # Build tool definition with proper parameter requirements
        tool_definition = {
            "name": workflow["name"].lower().replace(" ", "_"),
            "description": f"Trigger the '{workflow['name']}' workflow",
            "path": webhook_node['parameters']['path'] if webhook_node else "",
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
        
        # Add parameters to input schema
        for param, info in code_params.items():
            tool_definition["input_schema"]["properties"][param] = {
                "type": "string",
                "description": f"{param} parameter" + 
                              (f" (default: {info['default_value']})" if info['has_default'] else "")
            }
            if not info['has_default']:
                tool_definition["input_schema"]["required"].append(param)
                
        return tool_definition
```

### 3. ToolRegistry
Manages the collection of tools extracted from n8n workflows and handles tool execution.

```python
class ToolRegistry:
    def __init__(self, n8n_client: N8nClient = None, llm_client: LLMClient = None):
        self.n8n_client = n8n_client or N8nClient()
        self.llm_client = llm_client or LLMClient()
        self.tools = {}
        self._base_url = os.getenv("N8N_WEBHOOK_BASE_URL").rstrip('/')
        
    def refresh_tools(self) -> None:
        """Refresh tools from n8n workflows using LLM conversion"""
        workflows = self.n8n_client.get_workflows()
        for workflow in workflows:
            tool = self.convert_workflow_to_tool(workflow)
            if tool:
                self.tools[tool["name"]] = tool
                logger.info(f"Registered tool: {tool['name']} -> {tool['webhook_url']}")
    
    def convert_workflow_to_tool(self, workflow: Dict) -> Optional[Dict]:
        """Convert a workflow to a tool definition using the LLM"""
        try:
            tool = self.llm_client.convert_workflow_to_tool(workflow)
            if not tool:
                return None
                
            # Add webhook URL
            path = tool.get('path', '').lstrip('/')
            tool['webhook_url'] = f"{self._base_url}/{path}"
            
            return tool
            
        except Exception as e:
            logger.error(f"Error converting workflow to tool: {e}")
            return None
            
    def execute_tool(self, tool_name: str, params: Dict) -> Dict:
        """Execute a tool by name with the given parameters"""
        tool = self.tools.get(tool_name)
        if not tool:
            return {"status": "error", "message": f"Tool '{tool_name}' not found"}
            
        try:
            # The trigger_webhook method will automatically try both POST and GET methods
            result = self.n8n_client.trigger_webhook(tool['webhook_url'], params)
            logger.info(f"Tool execution completed for {tool_name}")
            return result
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}
```

### 4. Agent
Processes messages using LangGraph for a modern, graph-based agent architecture.

```python
class Agent:
    def __init__(self, tool_registry):
        self.tool_registry = tool_registry
        self.graph = self._create_agent_graph()
        
    def _create_agent_graph(self):
        """Create the n8n AI Agent graph using LangGraph"""
        graph = StateGraph(AgentState)
        graph.add_node("chatbot", self._chatbot)
        tool_node = ToolNode(self._convert_n8n_tools_to_langchain_tools())
        graph.add_node("tools", tool_node)
        
        # Add conditional routing between nodes
        graph.add_conditional_edges("chatbot", self._route_tools, {"tools": "tools", END: END})
        graph.add_edge("tools", "chatbot")
        
        return graph.compile()
        
    def process_message(self, message):
        """Process a message using the LangGraph agent"""
        # Create initial state with user message
        initial_state = {
            "messages": [HumanMessage(content=message)],
            "tools": self.tool_registry.get_tools()
        }
        
        # Run the graph and return response
        result = self.graph.invoke(initial_state)
```

## Message Flow

1. **Slack Message Reception**:
   - User sends message to Slack bot
   - SlackHandler passes message to Agent

2. **Tool Selection**:
   - Agent presents tools to LLM
   - LLM selects appropriate tool based on message
   - Agent extracts tool name and parameters

3. **Tool Execution**:
   - Agent retrieves tool definition from registry
   - Agent triggers webhook with parameters
   - n8n handles the workflow execution
   - n8n sends response directly to Slack

## Workflow to Tool Conversion

### Example Workflow (n8n-workflow.json)
```json
{
  "data": [
    {
      "id": "bVnibKAJuIQVG5TV",
      "name": "My workflow",
      "nodes": [
        {
          "parameters": {
            "path": "emails",
            "options": {}
          },
          "type": "n8n-nodes-base.webhook",
          "name": "Webhook"
        },
        {
          "parameters": {
            "jsCode": "const emails = items[0].json.body.emails;\n\nreturn emails.map(email => {\n  return {\n    json: {\n      email: email.trim()\n    }\n  };\n});\n"
          },
          "type": "n8n-nodes-base.code",
          "name": "Code"
        }
      ]
    }
  ]
}
```

### Converted Tool (tools.json)
```json
{
  "name": "my_workflow",
  "auth_key": "",
  "parameters": [
    {
      "name": "emails",
      "type": "array",
      "items": {"type": "string"},
      "required": true,
      "description": "One or more email addresses to process"
    }
  ],
  "description": "Process a list of email addresses",
  "webhook_url": "https://n8n-app-young-feather-1595.fly.dev/emails"
}
```

## Implementation Steps

1. **Update N8nClient** to use the correct API endpoints:
   - Change from `/rest/workflows` to `/api/v1/workflows`
   - Update authentication header

2. **LLM-Powered Workflow Conversion**:
   - Fetch workflows from n8n API
   - Submit workflows to Claude LLM for analysis
   - Ask Claude to convert workflows directly to LangGraph tool format
   - Parse LLM response and create LangGraph-compatible tools
   - Provide Claude with LangGraph tool schema as reference

3. **Modify ToolRegistry** to use n8n workflows:
   - Remove Supabase dependency
   - Add workflow-to-tool conversion
   - Simplify organization handling

4. **Update Agent** to use LangGraph architecture:
   - Replace custom agent with LangGraph-based implementation
   - Use proper state management and graph-based execution
   - Convert n8n tools to LangChain tools
   - Implement conditional routing between nodes

## Reused Components

The implementation will reuse these existing components:
- `src/webhook/client.py` for webhook execution
- `src/agent/tools.py` for tool handling
- `src/slack/handlers.py` for Slack integration
- `src/agent/n8n_integration.py` for n8n API communication

## Configuration

```
# n8n Configuration
N8N_API_KEY=your-n8n-api-key
N8N_BASE_URL=https://n8n-app-young-feather-1595.fly.dev

# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_SIGNING_SECRET=your-slack-signing-secret

# LLM Configuration
CLAUDE_API_KEY=your-claude-api-key
CLAUDE_MODEL=claude-3-opus-20240229
```

## Webhook URL Handling

### Environment Variable Configuration

The system uses environment variables to manage webhook URLs, specifically:

```
N8N_WEBHOOK_BASE_URL=https://n8n-app-young-feather-1595.fly.dev/
```

This approach avoids hardcoding URLs in the codebase and allows for easy configuration changes.

### Dynamic URL Construction

The system dynamically constructs webhook URLs by combining:
1. The base URL from the environment variable (`N8N_WEBHOOK_BASE_URL`)  
2. The path extracted from the workflow data

Example:
```python
base_url = os.getenv("N8N_WEBHOOK_BASE_URL", "https://n8n-app-young-feather-1595.fly.dev")
base_url = base_url.rstrip("/")
webhook_url = f"{base_url}/{webhook_path}"
```

### Path Extraction Logic

The system extracts webhook paths from workflow data by:
1. Looking for the `parameters.path` property in webhook nodes
2. Properly handling leading slashes for consistent URL construction
3. Using fallback mechanisms if the path isn't found

### Error Handling

The webhook handling includes robust error handling:
1. Trying both POST and GET methods if one fails
2. Adding detailed logging for troubleshooting
3. Providing warnings about workflow activation requirements

Example endpoint: `https://n8n-app-young-feather-1595.fly.dev/webhook-test/emails`
