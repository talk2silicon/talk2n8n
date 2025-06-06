"""Tests for the ToolRegistry class."""
import json
import os
from unittest.mock import MagicMock, patch

import pytest

from src.n8n.tool_registry import ToolRegistry
from src.n8n.workflow_converter import WorkflowConverter
from src.n8n.tool_factory import ToolFactory
from src.n8n.client import N8nClient


def test_tool_registry_initialization():
    """Test that ToolRegistry initializes with default dependencies."""
    registry = ToolRegistry()
    
    assert registry is not None
    assert isinstance(registry.n8n_client, N8nClient)
    assert isinstance(registry.workflow_converter, WorkflowConverter)
    assert isinstance(registry.tool_factory, ToolFactory)


def test_tool_registry_with_custom_dependencies():
    """Test that ToolRegistry can be initialized with custom dependencies."""
    mock_client = MagicMock(spec=N8nClient)
    mock_converter = MagicMock(spec=WorkflowConverter)
    mock_factory = MagicMock(spec=ToolFactory)
    
    registry = ToolRegistry(
        n8n_client=mock_client,
        workflow_converter=mock_converter,
        tool_factory=mock_factory
    )
    
    assert registry.n8n_client is mock_client
    assert registry.workflow_converter is mock_converter
    assert registry.tool_factory is mock_factory


def test_refresh_tools_no_workflows():
    """Test refresh_tools when no workflows are found."""
    mock_client = MagicMock(spec=N8nClient)
    mock_client.get_workflows.return_value = []
    
    registry = ToolRegistry(n8n_client=mock_client)
    registry.refresh_tools()
    
    assert len(registry.get_tools()) == 0


def test_refresh_tools_with_workflows():
    """Test refresh_tools with workflows to convert."""
    # Setup test data
    workflow = {
        "id": "1",
        "name": "Test Workflow",
        "nodes": [
            {
                "type": "n8n-nodes-base.webhook",
                "parameters": {"path": "/test"}
            }
        ]
    }
    
    tool_definition = {
        "name": "test_tool",
        "description": "A test tool",
        "path": "/test"
    }
    
    # Setup mocks
    mock_client = MagicMock(spec=N8nClient)
    mock_client.get_workflows.return_value = [workflow]
    
    mock_converter = MagicMock(spec=WorkflowConverter)
    mock_converter.convert.return_value = tool_definition
    
    mock_factory = MagicMock(spec=ToolFactory)
    mock_factory.create_tools_from_definitions.return_value = {"test_tool": {"name": "test_tool"}}
    
    # Test
    registry = ToolRegistry(
        n8n_client=mock_client,
        workflow_converter=mock_converter,
        tool_factory=mock_factory
    )
    
    registry.refresh_tools()
    
    # Verify
    mock_converter.convert.assert_called_once_with(workflow)
    mock_factory.create_tools_from_definitions.assert_called_once_with(
        [tool_definition],
        webhook_base_url=registry._base_url,
        env=registry._env
    )
    assert len(registry.get_tools()) == 1
    assert registry.get_tool("test_tool") == {"name": "test_tool"}


def test_execute_tool_success():
    """Test successful tool execution."""
    mock_tool = {
        "name": "test_tool",
        "execute": MagicMock(return_value={"result": "success"})
    }
    
    registry = ToolRegistry()
    registry._tools = {"test_tool": mock_tool}
    
    result = registry.execute_tool("test_tool", param1="value1")
    
    mock_tool["execute"].assert_called_once_with(param1="value1")
    assert result == {"result": "success"}


def test_execute_tool_not_found():
    """Test executing a non-existent tool raises an error."""
    registry = ToolRegistry()
    
    with pytest.raises(ValueError, match="Tool 'missing_tool' not found"):
        registry.execute_tool("missing_tool")


def test_execute_tool_no_execute_method():
    """Test executing a tool with no execute method raises an error."""
    registry = ToolRegistry()
    registry._tools = {"bad_tool": {"name": "bad_tool"}}
    
    with pytest.raises(ValueError, match="Tool 'bad_tool' has no executable method"):
        registry.execute_tool("bad_tool")
