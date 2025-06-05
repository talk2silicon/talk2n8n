# n8n LLM Autonomy Agent — Design & Knowledge Base

**Last Updated: May 10, 2025 (13:37)**

## 1. Project Objective
- Refactor the n8n LLM autonomy agent to use only Anthropic Claude as the LLM.
- Remove OpenAI dependencies.
- Simplify the codebase and environment setup.
- Enable dynamic workflow integration with n8n via webhooks.
- Support robust parameter passing and dynamic tool docstrings for LLM reasoning.
- Provide a testing and debugging framework for integration.
- Integrate with Slack to enable user interaction through chat interface.

---

## 2. Environment & Configuration
- **.env** variables:
    - `CLAUDE_API_KEY` — Anthropic Claude API key
    - `CLAUDE_MODEL` — Model name (default: `claude-3-opus-20240229`)
    - `N8N_WEBHOOK_BASE_URL` — n8n webhook base URL
    - `N8N_API_KEY` — (optional, for authenticated n8n API usage)
    - `SUPABASE_URL` / `SUPABASE_KEY` — (optional, for Supabase integration)
    - `SLACK_BOT_TOKEN` — Slack bot token for API access
    - `SLACK_SIGNING_SECRET` — For verifying Slack requests
    - `N8N_SLACK_RESPONSE_WEBHOOK` — n8n webhook for sending responses back to Slack
    - `WORKSPACE_MAPPING_FILE` — Path to JSON file mapping Slack team IDs to organization IDs
    - `DEFAULT_ORGANIZATION_ID` — Fallback organization ID if mapping not found
- All OpenAI references and keys have been removed.
- API keys are loaded securely using `python-dotenv`.

---

## 3. Dynamic Workflow Integration
- Workflows are defined in `config/workflows.json`.
- Each workflow specifies:
    - `name`, `description`, `webhook_url`, `auth_key`, `required_inputs` (with type, description, required)
- The agent dynamically generates tool docstrings and schemas from the registry at runtime, so the LLM always knows available workflows and required parameters.
- The agent uses a closure pattern for tool registration, allowing dependency injection and dynamic documentation.

---

## 4. Parameter Passing & Webhook Triggering
- The agent parses user prompts, extracts relevant parameters, and passes them to the webhook as top-level fields.
- Debug logging is present at all key points:
    - Parameters provided by the LLM
    - Workflow and webhook URL
    - Required vs. provided inputs
    - Webhook payload and response
- The webhook client now detects and corrects nested parameters (e.g., if LLM passes `{kwargs: {...}}`).
- Any missing required parameter is reported back to the user with a clarifying prompt.

---

## 5. Dynamic Template Selection (SendGrid Example)
- For email workflows, a `template_id` or similar parameter can be included in the workflow definition.
- The LLM can map user intent (e.g., "send onboarding email") to a specific template via a mapping dictionary or prompt engineering.
- The agent can generalize from similar user prompts (e.g., "welcome pack", "getting started email") to the correct template.
- If ambiguous, the agent can ask the user to clarify which template to use.

---

## 6. Claude API Integration & Error Handling
- The agent uses the latest `langchain-anthropic` package, with correct parameter names (`api_key`).
- Enhanced error handling and debug logging for authentication errors, rate limiting, and API schema mismatches.
- The tool schema format uses `schema` (not `input_schema`) for Claude compatibility.

---

## 7. Multi-Tenant Support & Organization ID
- The system supports multi-tenancy through organization IDs in Supabase.
- Default organization ID for testing: `f16e946d-4474-4a56-b434-a321629d50e4`
- Workflows are filtered by organization ID when loaded from Supabase.
- The `WorkflowRegistry` class stores the organization ID as `organization_id`.
- The `WebhookClient` accesses this attribute when triggering workflows.
- Fixed an attribute mismatch issue where `WebhookClient` was trying to access `organization` instead of `organization_id`.

## 8. Key Memories & Learnings
- **Claude API integration**: Fixed by using correct schema format and parameter names.
- **Webhook parameter passing**: Fixed nested `kwargs` issue by flattening parameters before sending to webhook.
- **Dynamic tool docstrings**: Tool docstrings are generated at runtime from the workflow registry, so the LLM always has up-to-date context.
- **Debugging approach**: Extensive logging at all levels (agent, tool, webhook client) to trace parameter flow and webhook execution.
- **Template mapping**: LLM is capable of mapping similar user prompts to the correct template, especially with good prompt engineering and schema documentation.
- **Organization attribute fix**: Updated the webhook client to use `getattr(workflow_registry, 'organization_id', None)` for better compatibility.

---

## 9. Testing Scripts & Workflow Execution
- **test_supabase_tools.py**: Tests loading workflows from Supabase and presenting them as tools to the LLM.
- **test_workflow_execution.py**: Tests the full flow from user prompt to webhook execution (requires `src.llm.claude_client` module).
- **test_full_flow.py**: Similar to test_workflow_execution but with a different implementation.
- **test_supabase_agent.py**: Comprehensive test for the agent with Supabase integration.

To test the full path from prompt to webhook execution:
```bash
python test_supabase_agent.py --org-id f16e946d-4474-4a56-b434-a321629d50e4 --test-type single --message "Create a student account for Jane Smith with email jane.smith@example.com"
```

## 10. Slack Integration with Dynamic Tools
- The system integrates with Slack to allow users to interact with n8n workflows through a Slack bot.
- **Simple Threading Approach**:
  - Slack events API sends messages to our HTTP server
  - Server acknowledges immediately with 200 OK
  - Processing happens in a thread pool (concurrent.futures.ThreadPoolExecutor)
  - Responses are sent back to Slack using n8n webhook

### Slack Bot Architecture
- **Components**:
  - FastAPI server for receiving Slack events
  - Thread pool for asynchronous processing
  - n8n webhook for sending responses back to Slack
  - Mapping between Slack team IDs and organization IDs
  - LangGraph-based agent with dynamic tools loaded from Supabase

### Implementation Details
- **Slack Message Flow**:
  1. User sends message to Slack bot
  2. Slack forwards event to our FastAPI server
  3. Server verifies Slack signature and acknowledges receipt
  4. Message is processed in a background thread using the LangGraph agent
  5. Agent loads dynamic tools from Supabase based on organization ID
  6. Agent processes the message and executes tools as needed
  7. Response is sent back to Slack via n8n webhook

- **Dynamic Tools Implementation**:
  - Tools are loaded from Supabase at runtime based on organization ID
  - Each tool corresponds to an n8n workflow with a webhook URL
  - Tools are presented to the Claude LLM using the native LangChain binding mechanism
  - No OpenAI function conversion is needed - tools work directly with Claude API
  - Hardcoded tools (like the weather tool) can be added for testing purposes

- **Organization Mapping**:
  - Simple JSON file maps Slack team IDs to organization IDs
  - Format: `{"T12345": "f16e946d-4474-4a56-b434-a321629d50e4", ...}`
  - Fallback to default organization ID if mapping not found

- **Security**:
  - Slack request signature verification
  - Rate limiting to prevent abuse
  - Secure storage of Slack API tokens

## 11. Troubleshooting & Next Steps
- If a webhook fails, logs will show all parameters and responses for diagnosis.
- For complex workflows (e.g., dynamic template selection), consider exposing a tool to list available templates or clarify ambiguous requests.
- Continue to expand workflows and test with varied user prompts to ensure robust LLM reasoning and parameter extraction.
- Enhanced logging has been added to troubleshoot tool binding and execution issues.
- Test scripts have been created to validate both hardcoded and dynamic tools:
  - `test_weather_tool.py`: Tests the hardcoded weather tool and dynamic tools from Supabase
  - `test_dynamic_tools.py`: Tests loading and executing dynamic tools from Supabase
- For production scaling of Slack integration, consider upgrading to Redis-based task queue.

## 12. Claude API Integration Fixes
- Fixed the Claude API integration by using the correct tool binding approach:
  - Removed the OpenAI function conversion step that was causing issues
  - Used the native LangChain `bind_tools` method directly with the tools list
  - Updated the tool schema format from `input_schema` to `schema` for Claude compatibility
- Enhanced error handling in the agent to better capture API-related issues:
  - Authentication errors
  - Rate limiting
  - Quota exceeded scenarios
  - Schema format errors
- Added detailed logging to help diagnose issues with tool presentation to the LLM

---

*This document captures the current design, knowledge, and operational memory of the n8n LLM autonomy agent as of 2025-05-09. Update as new workflows, integrations, or design patterns are added.*

## 13. Testing and Debugging

### Test Scripts
- **test_weather_tool.py**: Interactive CLI for testing both hardcoded and dynamic tools
- **test_dynamic_tools.py**: Tests loading dynamic tools from Supabase
- **interactive_chat.py**: Simple CLI chat interface for testing the agent without Slack

### Debugging Tools
- Enhanced logging throughout the codebase:
  - Tool loading and binding
  - Webhook execution
  - LLM interactions
  - Error handling
- Detailed error messages for common failure scenarios

### Common Issues and Solutions

#### Tool Execution Issues
- Missing environment variables (N8N_WEBHOOK_BASE_URL, CLAUDE_API_KEY)
- Incorrect webhook URL format in workflow definitions
- Insufficient permissions for webhook endpoints
- Rate limiting or timeout issues with n8n server

#### Authentication Issues
- Missing or expired API keys
- Incorrect signing secrets for Slack verification
- Missing or invalid authentication headers for n8n webhooks
- **400 Bad Request from Claude API**: Usually related to incorrect tool schema format. Make sure to use `schema` instead of `input_schema`.
- **Tools not executing**: Check that the tools are properly bound to the model and that the LLM is correctly identifying when to use them.
- **Webhook failures**: Verify the webhook URL is correct and accessible, and that all required parameters are being passed correctly.

## 14. Slack Integration Improvements

### Recent Enhancements
- **System Prompt Optimization**: Updated the system prompt to explicitly instruct Claude to use tool calls with proper formatting:
  - Added clear instructions for tool usage with examples
  - Included specific guidance for handling Slack's special formatting (e.g., `<mailto:email@example.com|email@example.com>` format)
  - Added examples showing correct tool usage patterns

### Key Fixes
- **Removed Hardcoded Tools**: Completely removed all hardcoded tools (e.g., `get_weather`) from the Slack integration:
  - Modified `create_agent_graph` to only use dynamic tools loaded from Supabase
  - Ensured that only dynamic tools are bound to the LLM during Slack interactions
  - Updated logging to reflect dynamic tool usage

- **Slack Message Formatting**: Improved handling of Slack's special message formats:
  - Added regex patterns to extract emails from `<mailto:email@example.com|email@example.com>` format
  - Added handling for user mentions and URL formats
  - Enhanced the system prompt to instruct Claude to handle these formats directly

- **LLM Configuration Optimization**:
  - Set temperature to 0.0 for maximum determinism and reliable tool usage
  - Ensured consistent LLM configuration between interactive chat and Slack integration

- **Parameter Transformation**:
  - Added automatic transformation of parameters to match expected formats
  - Implemented conversion from `to` parameter to `emails` array for email workflows
  - Added validation to ensure email parameters are always formatted as arrays

## 15. Frontend Development Considerations

### React Core Concepts for MVP

1. **Component-Based Architecture**
   - Building UI as isolated, reusable components
   - Each component manages its own state and rendering
   - Enables composition and reusability

2. **Declarative Paradigm**
   - Describe what the UI should look like, not how to achieve it
   - React handles DOM updates efficiently through reconciliation

3. **Unidirectional Data Flow**
   - Data flows down from parent to child components through props
   - State changes flow back up through callbacks
   - Makes application behavior predictable and easier to debug

4. **State Management**
   - Local component state with useState hook
   - Context API for sharing state across components
   - Consider external state management (Redux, Zustand) for complex applications

5. **Hooks**
   - useState: Manage state in functional components
   - useEffect: Handle side effects (API calls, subscriptions)
   - useContext: Access context without nesting
   - useRef: Reference DOM elements or persist values

### Shadcn UI Evaluation

**Recommendation**: Shadcn UI is an excellent choice for the MVP frontend due to its flexibility, modern design, and copy-paste component approach.

**Pros**:
- **Copy-Paste Components**: Install components directly into your project for full code control
- **Highly Customizable**: Built on Tailwind CSS and Radix UI primitives
- **Accessibility-Focused**: Strong accessibility features through Radix UI
- **Framework Agnostic**: Works with React, Next.js, Astro, Remix, and other frameworks
- **Modern Design**: Clean, professional aesthetic following current design trends
- **Growing Community**: 40k+ GitHub stars and active development
- **No Version Lock-In**: Own the component code, no dependency on package updates

**Cons**:
- **Not a Traditional Library**: Requires understanding its copy-paste approach
- **Tailwind Dependency**: Requires Tailwind CSS knowledge
- **Bundle Size Consideration**: Be selective about which components you add
- **Relatively New**: Released in March 2023

**Implementation Approach**:
```bash
# Install in a Next.js project
npx shadcn-ui@latest init

# Add components as needed
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
```

## 16. Testing with Hardcoded and Dynamic Tools

### Current Implementation Status

The current implementation correctly handles both hardcoded tools and dynamic tools loaded from Supabase. The workflow JSON to tool conversion logic is working as expected. When the LLM decides to use a tool, the appropriate function is called, but there may be issues with how the webhook is triggered or how the results are returned.

### Debugging Approach

1. **Enhanced Logging**: Add detailed logging at each step of the tool execution process to identify where failures occur:
   - Log when a tool is selected by the LLM
   - Log the parameters passed to the tool
   - Log the webhook URL and payload
   - Log the response from the webhook

2. **Environment Variables**: Ensure all required environment variables are set:
   - `CLAUDE_API_KEY`: For Claude API access
   - `N8N_WEBHOOK_BASE_URL`: Base URL for n8n webhooks
   - `SUPABASE_URL` and `SUPABASE_KEY`: For Supabase access (if using dynamic tools)

3. **Webhook Testing**: Use tools like Postman or curl to test webhooks directly before integrating with the LLM

### Using interactive_chat.py for Testing

The `interactive_chat.py` script can be used to test the core functionality without Slack integration. To test with both hardcoded and dynamic tools:

1. Modify the script to initialize both types of tools:

```python
# Load dynamic tools from Supabase or local file
workflow_registry = get_workflow_registry(organization_id)
dynamic_tools = create_workflow_tools(workflow_registry, webhook_client)

# Define hardcoded weather tool
def get_weather(location: str) -> dict:
    """Get the current weather for a location."""
    print(f"Getting weather for {location}")
    return {
        "status": "success",
        "message": f"Weather for {location}: 72°F, Sunny",
        "data": {
            "location": location,
            "temperature": 72,
            "condition": "Sunny"
        }
    }

# Combine both types of tools
all_tools = dynamic_tools + [get_weather]

# Create agent with all tools
agent = create_agent_graph(all_tools)
```

2. Run the script and test both tool types:
   - Test the hardcoded weather tool: "What's the weather in New York?"
   - Test a dynamic tool from Supabase: "Send an email to test@example.com"

3. Check the logs to see if tools are being executed correctly

### Common Testing Issues

1. **Tool Not Found**: Ensure the tool name in the LLM response matches exactly with the function name
2. **Parameter Mismatch**: Ensure the parameters expected by the tool match what the LLM is providing
3. **Webhook Connection**: Verify the n8n server is running and accessible
4. **Authentication**: Check if authentication is required for the webhook

The current implementation is correct in terms of tool definition and LLM integration. Focus debugging efforts on the webhook execution and response handling.
