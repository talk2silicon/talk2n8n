"""
Graph structure for the n8n AI Agent.

This module implements an agent that can process natural language messages,
interact with n8n workflows, and execute tools based on user requests.
"""

# Standard library imports
import logging
import os
from typing import Annotated, Optional, Sequence, TypedDict

# Third-party imports
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain.tools import StructuredTool


# Local application imports
from talk2n8n.n8n.client import N8nClient
from talk2n8n.n8n.tool_service import ToolService


# Configure logging
from talk2n8n.config.settings import settings


def json_schema_to_pydantic_model(schema: dict, model_name: str = "ToolParams"):
    """Convert JSON schema to Pydantic model for tool argument validation."""
    from pydantic import Field, create_model

    type_map = {
        "string": str,
        "integer": int,
        "boolean": bool,
        "number": float,
    }

    required = set(schema.get("required", []))
    properties = schema.get("properties", {})

    model_fields = {}
    for prop, prop_schema in properties.items():
        typ = type_map.get(prop_schema.get("type"), str)
        desc = prop_schema.get("description", "")
        if prop in required:
            model_fields[prop] = (typ, Field(description=desc))
        else:
            model_fields[prop] = (typ, Field(default=None, description=desc))

    return create_model(model_name, **model_fields)  # type: ignore


logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("agent_debug.log")],
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

    def __init__(
        self,
        llm: Optional[BaseChatModel] = None,
        n8n_base_url: Optional[str] = None,
        n8n_api_key: Optional[str] = None,
    ):
        """
        Initialize the agent with an optional LLM and n8n configuration.

        Args:
            llm: The language model to use (default: ChatAnthropic with claude-3-opus-20240229)
            n8n_base_url: Base URL of the n8n instance (default: from N8N_WEBHOOK_BASE_URL env var)
            n8n_api_key: API key for n8n (default: from N8N_API_KEY env var)
        """
        # Set up the LLM
        from pydantic.v1.types import SecretStr

        api_key = os.getenv("CLAUDE_API_KEY")
        api_key_secret = SecretStr(api_key) if api_key is not None else None
        self.llm = llm or ChatAnthropic(
            model_name=os.getenv("CLAUDE_MODEL", "claude-3-opus-20240229"),
            temperature=0.0,
            api_key=api_key_secret.get_secret_value() if api_key_secret else None,  # type: ignore
            timeout=60,
            stop=None,
            base_url=None,
        )

        # Initialize n8n client
        self.n8n_client = N8nClient(
            base_url=n8n_base_url or os.getenv("N8N_WEBHOOK_BASE_URL"),
            api_key=n8n_api_key or os.getenv("N8N_API_KEY"),
        )

        # Initialize tool service with LLM
        self.tool_service = ToolService(n8n_client=self.n8n_client, llm=self.llm)

        # Initialize the graph
        self._initialize_graph()

        logger.info("Agent initialized with LLM: %s", self.llm.__class__.__name__)

    def _initialize_graph(self):
        """Initialize LangGraph state machine for the agent."""
        # Implementation details...

        logger.info(
            "ToolService initialized with n8n_base_url: %s, api_key: %s",
            self.n8n_client.base_url,
            self.n8n_client.api_key,
        )

        # Refresh tools from n8n
        self.tool_service.sync_workflows()
        logger.info("Creating LangGraph with the tools from the tool service")
        self.graph = self._create_agent_graph()

    def _create_agent_graph(self):
        """Create the n8n AI Agent graph using the standard LangGraph pattern."""
        # Create agent graph

        # Create the graph
        graph = StateGraph(AgentState)

        # Add nodes
        graph.add_node("chatbot", self._chatbot)

        # Get tools from the service
        n8n_tools = self.tool_service.list_tools()

        langchain_tools = []

        for tool_def in n8n_tools:
            tool_name = tool_def.get("name")
            tool_description = tool_def.get("description", "")

            # Build Pydantic model from input_schema
            input_schema = tool_def.get("input_schema") or tool_def.get("parameters")
            if input_schema is None or not isinstance(input_schema, dict):
                continue
            args_model = json_schema_to_pydantic_model(
                input_schema, model_name=str(tool_name).title() + "Params"
            )

            def make_tool_executor(tool_name):
                def execute_tool(**kwargs):
                    logging.info(f"Calling tool '{tool_name}' with kwargs: {kwargs}")
                    result = self.tool_service.execute_tool(tool_name, kwargs)
                    return result

                return execute_tool

            if not isinstance(tool_name, str):
                continue
            langchain_tool = StructuredTool(
                name=tool_name,
                description=tool_description,
                args_schema=args_model,
                func=make_tool_executor(tool_name),
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

        # Compile the graph and return the compiled version
        compiled_graph = graph.compile()
        return compiled_graph

    def _chatbot(self, state: AgentState):
        """Process the user message and generate a response."""
        messages = state["messages"]

        # Get the tools from the registry
        tools = self.tool_service.list_tools()

        # Tools are already in Claude format from ToolService
        anthropic_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"],
                },
            }
            for tool in tools
        ]

        # Call Claude
        try:
            # Bind tools to the model
            model_with_tools = self.llm.bind_tools(anthropic_tools)

            # Add system prompt if not present
            if not any(isinstance(msg, SystemMessage) for msg in messages):
                messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)

            # Invoke the model and return updated state
            response = model_with_tools.invoke(messages)
            return {"messages": list(messages) + [response]}
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "messages": list(messages)
                + [HumanMessage(content=f"Error processing your request: {str(e)}")]
            }

    def _route_tools(self, state: AgentState):
        """Route to tools node if tool calls are present, otherwise end the conversation."""
        if not (messages := state.get("messages", [])):
            raise ValueError("No messages found in state")

        ai_message = messages[-1]

        # Count tool calls to prevent infinite loops
        tool_call_count = sum(
            1 for msg in messages if hasattr(msg, "tool_calls") and msg.tool_calls
        )

        # Limit maximum tool calls
        MAX_TOOL_CALLS = 10
        if tool_call_count >= MAX_TOOL_CALLS:
            logger.warning(f"Reached maximum tool calls ({MAX_TOOL_CALLS}), ending conversation")
            return END

        # Check if the last message has tool calls
        if hasattr(ai_message, "tool_calls") and ai_message.tool_calls:
            return "tools"

        # No tool calls
        return END

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
            initial_state = {"messages": [HumanMessage(content=message)]}

            # Run the graph
            result = self.graph.invoke(initial_state)

            # Extract the response from the last AI message
            if messages := result.get("messages", []):
                for msg in reversed(messages):
                    if hasattr(msg, "content") and msg.content:
                        return str(msg.content)

            return "No response generated"

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return f"Error processing your request: {str(e)}"

    def refresh_tools(self) -> str:
        """
        Refresh tools from n8n workflows.

        Returns:
            A message indicating the result of the refresh operation
        """
        try:
            self.tool_service.sync_workflows()
            tools = self.tool_service.list_tools()
            self.graph = self._create_agent_graph()
            return f"Successfully refreshed tools. {len(tools)} tools available."
        except Exception as e:
            error_msg = f"Error refreshing tools: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg

    def run(self, message: str) -> str:
        """Process a message and return a response."""
        return self.process_message(message)
