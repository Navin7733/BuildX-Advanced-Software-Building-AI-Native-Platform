"""
Adapter to convert MCP tools into LangChain/LangGraph compatible tools.
"""
import logging
from typing import List, Callable, Any
from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel, create_model

from .client import MCPClient
from .registry import get_servers_for_agent, get_server_config

logger = logging.getLogger(__name__)


def create_mcp_tool(client: MCPClient, server_id: str, action: str, description: str = "") -> BaseTool:
    """Create a LangChain tool wrapper around an MCP action."""
    
    def mcp_tool_func(**kwargs) -> dict:
        """Executes the MCP tool call."""
        result = client.call(server_id, action, **kwargs)
        if not result['success']:
            return f"Error: {result['error']}"
        return result['result']

    # For a fully dynamic implementation, we would query the MCP server's schema
    # (using the `tools/list` protocol method) to build the precise Pydantic model.
    # For this MVP skeleton, we'll use a generic `kwargs` approach or simple dynamic model.
    
    # Generic model that accepts any kwargs (a bit loose, but works for MVP without introspection)
    class DynamicArgs(BaseModel):
        class Config:
            extra = 'allow'

    return StructuredTool.from_function(
        func=mcp_tool_func,
        name=f"{server_id}_{action}",
        description=description or f"Execute {action} on {server_id} MCP server.",
        args_schema=DynamicArgs,
    )


def get_tools_for_agent(agent_type: str, project_id: str, run_id: str) -> List[BaseTool]:
    """Get all LangChain-compatible tools that this agent is permitted to use via MCP."""
    client = MCPClient(agent_type, project_id, run_id)
    servers = get_servers_for_agent(agent_type)
    
    tools = []
    for server in servers:
        server_id = server['id']
        allowed_actions = server.get('allowed_actions', [])
        
        for action in allowed_actions:
            tools.append(create_mcp_tool(client, server_id, action))
            
    return tools
