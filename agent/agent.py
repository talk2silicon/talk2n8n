"""Graph structure for the n8n AI Agent."""

import os
import logging
from typing import Annotated, Sequence, TypedDict, Dict, Any, List, Optional

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from n8n.tool_registry import ToolRegistry

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('agent_debug.log')
    ]
)
logger = logging.getLogger(__name__)

# Define the system prompt
SYSTEM_PROMPT = """
You are an AI assistant that helps users interact with n8n workflows.
You have access to tools that can trigger these workflows via webhooks.

When a user asks you to perform a task:
1. Select the most appropriate tool based on the user's request
2. Only ask for parameters that are explicitly marked as required in the tool description
3. Do not ask for additional parameters like subject, body, or other fields unless they are listed as required
4. The n8n workflow will handle all additional processing once triggered

If no tool matches the user's request, respond conversationally and explain what you can help with.
"""

# Define the state schema using the standard LangChain pattern
class AgentState(TypedDict):
    """State for the n8n AI Agent."""
    messages: Annotated[Sequence[BaseMessage], add_messages]

class Agent:
    """Agent for processing messages and executing tools using LangGraph."""
    
    def __init__(self, tool_registry: ToolRegistry):
        """
        Initialize the agent.
        
        Args:
            tool_registry: Registry for n8n workflow tools
        """
        logger.info("Initializing Agent")
        self.tool_registry = tool_registry
        logger.debug(f"Tool registry initialized: {self.tool_registry}")
        
        # Download tools from n8n
        logger.info("Downloading tools from n8n")
        self.tool_registry.refresh_tools()
        
        # Create the graph with the tools from the registry
        logger.info("Creating LangGraph with the tools from the registry")
        self.graph = self._create_agent_graph()
    
    def _create_agent_graph(self) -> StateGraph:
        """Create the n8n AI Agent graph using the standard LangGraph pattern."""
        logger.info("Creating n8n AI Agent graph")
        
        # Create the graph
        graph = StateGraph(AgentState)
        
        # Add nodes
        graph.add_node("chatbot", self._chatbot)
        
        # Get tools from the registry
        n8n_tools = self.tool_registry.get_tools()
        logger.info(f"Creating ToolNode with {len(n8n_tools)} tools from the registry")
        
        # Create LangChain tools directly from the registry tools
        from langchain_core.tools import Tool
        langchain_tools = []
        
        for tool_def in n8n_tools:
            tool_name = tool_def.get('name')
            tool_description = tool_def.get('description', '')
            
            # Create a function to execute the tool
            def make_tool_executor(tool_name):
                def execute_tool(*args, **kwargs):
                    logger.info(f"[Tool: {tool_name}] Called with args: {args}, params: {kwargs}")
                    # Process parameters to handle different formats
                    processed_kwargs = self._process_tool_parameters(tool_name, kwargs)
                    logger.info(f"[Tool: {tool_name}] Processed params: {processed_kwargs}")
                    return self.tool_registry.execute_tool(tool_name, processed_kwargs)
                return execute_tool
            
            # Create the tool
            langchain_tool = Tool(
                name=tool_name,
                description=tool_description,
                func=make_tool_executor(tool_name)
            )
            
            langchain_tools.append(langchain_tool)
        
        # Create the ToolNode with the tools
        tool_node = ToolNode(langchain_tools)
        graph.add_node("tools", tool_node)
        
        # Set entry point
        graph.set_entry_point("chatbot")
        
        # Add conditional edge from chatbot to either tools or END
        graph.add_conditional_edges(
            "chatbot",
            self._route_tools,
            {"tools": "tools", END: END},
        )
        
        # Any time a tool is called, we return to the chatbot to decide the next step
        graph.add_edge("tools", "chatbot")
        graph.add_edge(START, "chatbot")
        
        # Compile the graph
        return graph.compile()
    
    def _chatbot(self, state: AgentState):
        """Process the user message and generate a response."""
        logger.info("Chatbot processing message")
        
        messages = state["messages"]
        
        # Get API credentials from environment
        api_key = os.environ.get("CLAUDE_API_KEY")
        if not api_key:
            raise ValueError("Claude API key not provided and CLAUDE_API_KEY environment variable not set")
        
        model_name = os.environ.get("CLAUDE_MODEL", "claude-3-opus-20240229")
        
        # Initialize the model
        model = ChatAnthropic(
            anthropic_api_key=api_key,
            model=model_name,
            temperature=0
        )
        
        # Get the tools from the registry
        tools = self.tool_registry.get_tools()
        logger.info(f"Using {len(tools)} tools from the registry")
        
        # Debug: Print the exact format of the tools
        import json
        logger.info(f"Tool format: {json.dumps(tools, indent=2)}")
        
        # Create a copy of tools without internal fields
        anthropic_tools = []
        for tool in tools:
            anthropic_tool = {
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool["input_schema"]
            }
            anthropic_tools.append(anthropic_tool)
        
        # Print the exact payload that will be sent to Anthropic
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)
        
        # Create the request payload
        payload = {
            "model": model_name,
            "messages": [msg.dict() if hasattr(msg, "dict") else {"role": msg.type, "content": msg.content} for msg in messages],
            "tools": anthropic_tools,
            "max_tokens": 1024,
            "temperature": 0
        }
        
        # Print the exact payload
        logger.info(f"Anthropic API payload: {json.dumps(payload, indent=2)}")
        
        # Bind tools to the model
        model_with_tools = model.bind_tools(anthropic_tools)
        
        # Add system prompt if not present
        if not any(isinstance(msg, SystemMessage) for msg in messages):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)
        
        # Invoke the model and return updated state
        response = model_with_tools.invoke(messages)
        return {"messages": messages + [response]}
    
    def _route_tools(self, state: AgentState):
        """Route to tools node if tool calls are present, otherwise end the conversation."""
        if not (messages := state.get("messages", [])):
            raise ValueError("No messages found in state")
            
        ai_message = messages[-1]
        
        # Count tool calls to prevent infinite loops
        tool_call_count = sum(
            1 for msg in messages 
            if hasattr(msg, "tool_calls") and msg.tool_calls
        )
        
        # Limit maximum tool calls
        MAX_TOOL_CALLS = 10
        if tool_call_count >= MAX_TOOL_CALLS:
            logger.warning(f"Reached maximum tool calls ({MAX_TOOL_CALLS}), ending conversation")
            return END
        
        # Check if the last message has tool calls
        if hasattr(ai_message, "tool_calls") and ai_message.tool_calls:
            # Log the tool calls for debugging
            for tool_call in ai_message.tool_calls:
                # Handle different tool call formats (dict or object)
                if isinstance(tool_call, dict):
                    tool_name = tool_call.get('name', 'unknown')
                    tool_args = tool_call.get('args', {})
                    logger.info(f"Tool call detected: {tool_name} with args: {tool_args}")
                else:
                    # Assume it's an object with attributes
                    try:
                        tool_name = getattr(tool_call, 'name', 'unknown')
                        tool_args = getattr(tool_call, 'args', {})
                        logger.info(f"Tool call detected: {tool_name} with args: {tool_args}")
                    except Exception as e:
                        logger.error(f"Error accessing tool call attributes: {e}")
                        logger.debug(f"Tool call object: {repr(tool_call)}")
            return "tools"
        
        logger.info("No tool calls detected, ending conversation")
        return END
    
    def _process_tool_parameters(self, tool_name: str, kwargs: dict) -> dict:
        """Process tool parameters to handle different formats from the LLM.
        
        Args:
            tool_name: Name of the tool being executed
            kwargs: Parameters passed to the tool
            
        Returns:
            Processed parameters with correct types
        """
        # Get the tool definition from the registry
        tool_def = self.tool_registry.get_tool(tool_name)
        if not tool_def:
            logger.warning(f"Tool {tool_name} not found in registry")
            return kwargs
            
        parameters = tool_def.get("parameters", [])
        processed_kwargs = {}
        
        for param in parameters:
            param_name = param.get("name")
            param_type = param.get("type", "string")
            
            # Skip if parameter not provided
            if param_name not in kwargs:
                continue
            
            value = kwargs.get(param_name)
            
            # Handle array type parameters - convert string representations to actual lists
            if param_type == "array" and isinstance(value, str):
                # Try to handle various string formats the LLM might use
                if value.startswith('[') and value.endswith(']'):
                    # Remove brackets and split by comma
                    try:
                        # Try to parse as JSON first
                        import json
                        processed_value = json.loads(value)
                    except json.JSONDecodeError:
                        # Fallback to simple parsing
                        items = value[1:-1].split(',')
                        processed_value = [item.strip().strip('"').strip('\'') for item in items if item.strip()]
                else:
                    # Treat as a single item list
                    processed_value = [value]
                processed_kwargs[param_name] = processed_value
            else:
                # Pass through other types unchanged
                processed_kwargs[param_name] = value
        
        return processed_kwargs

    
    def process_message(self, message: str) -> str:
        """
        Process a message and return a response.
        
        Args:
            message: User message
            
        Returns:
            Response from the LLM or tool execution
        """
        try:
            # Create initial state with the user message
            initial_state = {
                "messages": [HumanMessage(content=message)]
            }
            
            # Run the graph
            result = self.graph.invoke(initial_state)
            
            # Extract the response from the last AI message
            if messages := result.get("messages", []):
                for msg in reversed(messages):
                    if hasattr(msg, "content") and msg.content:
                        return msg.content
            
            return "No response generated"
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return f"Error processing your request: {str(e)}"
    
    async def process_message_async(self, message: str) -> str:
        """
        Process a message asynchronously.
        
        Args:
            message: The message to process
            
        Returns:
            The response from the agent
        """
        logger.info(f"Processing message: {message}")
        
        try:
            # Create initial state
            state = AgentState({"messages": [HumanMessage(content=message)]})
            logger.debug(f"Initial state: {state}")
            
            # Run the graph
            logger.info("Invoking agent graph")
            final_state = await self.graph.ainvoke(state)
            logger.debug(f"Final state: {final_state}")
            
            # Get the last message
            response = final_state["messages"][-1].content
            logger.info(f"Agent response: {response}")
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return f"Error processing your request: {str(e)}"
            
    def refresh_tools(self) -> str:
        """
        Refresh tools from n8n workflows.
        
        Returns:
            A message indicating the result of the refresh operation
        """
        try:
            logger.info("Manually refreshing tools from n8n workflows")
            
            # Download tools from n8n
            self.tool_registry.refresh_tools()
            
            # Get the updated tools
            tools = self.tool_registry.get_tools()
            tool_count = len(tools)
            
            # Log the available tools for debugging
            for tool in tools:
                logger.info(f"Refreshed tool: {tool.get('name')} | {tool.get('description')}")
            
            # Rebuild the agent graph with the new tools
            self.graph = self._create_agent_graph()
            
            message = f"Successfully refreshed tools. {tool_count} tools available."
            logger.info(message)
            return message
        except Exception as e:
            error_msg = f"Error refreshing tools: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg
