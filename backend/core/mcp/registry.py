"""
MCP Server Registry
Defines all available MCP servers, their configurations,
allowed agents, and permitted tool actions.
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# ─── MCP Server Definitions ───────────────────────────────────────────────────
MCP_SERVERS = {
    "filesystem": {
        "id": "filesystem",
        "name": "Filesystem MCP Server",
        "description": "Read/write files in the project sandbox directory",
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem"],
        "env_extras": {},
        "allowed_agents": ["planner", "architect", "frontend", "backend_dev",
                           "reviewer", "testing", "documentation", "deployment", "memory"],
        "allowed_actions": ["read_file", "write_file", "list_directory",
                            "create_directory", "move_file", "search_files"],
        "rate_limit_per_run": 100,
    },

    "memory": {
        "id": "memory",
        "name": "BuildX Memory MCP Server",
        "description": "Store and retrieve project memories, decisions, and historical context",
        "transport": "python_module",
        "module": "core.mcp.servers.memory_server",
        "allowed_agents": ["planner", "architect", "frontend", "backend_dev",
                           "reviewer", "testing", "documentation", "deployment", "memory"],
        "allowed_actions": ["search_memories", "save_memory", "save_decision",
                            "get_decisions", "search_similar"],
        "rate_limit_per_run": 50,
    },

    "database": {
        "id": "database",
        "name": "Database MCP Server",
        "description": "Query and validate MongoDB schemas for project databases",
        "transport": "python_module",
        "module": "core.mcp.servers.database_server",
        "allowed_agents": ["backend_dev", "testing"],
        "allowed_actions": ["validate_schema", "run_query", "list_collections",
                            "seed_test_data", "get_schema"],
        "rate_limit_per_run": 20,
    },

    "github": {
        "id": "github",
        "name": "GitHub MCP Server",
        "description": "Interact with GitHub repositories — search, read files, create PRs",
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env_extras": {"GITHUB_PERSONAL_ACCESS_TOKEN": settings.MCP_GITHUB_TOKEN},
        "allowed_agents": ["architect", "reviewer", "documentation", "deployment"],
        "allowed_actions": ["search_repositories", "get_file_contents", "create_pull_request",
                            "push_files", "create_repository", "search_code"],
        "requires_config": ["MCP_GITHUB_TOKEN"],
        "rate_limit_per_run": 30,
    },

    "browser": {
        "id": "browser",
        "name": "Browser / Playwright MCP Server",
        "description": "Run browser tests, take screenshots, interact with UIs",
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@playwright/mcp@latest"],
        "allowed_agents": ["frontend", "testing"],
        "allowed_actions": ["screenshot", "navigate", "click", "fill",
                            "run_test", "evaluate"],
        "rate_limit_per_run": 10,
    },

    "deployment": {
        "id": "deployment",
        "name": "Deployment MCP Server",
        "description": "Deploy projects to Railway, Vercel, and Docker environments",
        "transport": "python_module",
        "module": "core.mcp.servers.deployment_server",
        "allowed_agents": ["deployment"],
        "allowed_actions": ["build_docker", "deploy_railway", "deploy_vercel",
                            "provision_infra", "get_deployment_status"],
        "requires_human_approval": True,
        "rate_limit_per_run": 5,
    },
}


def get_server_config(server_id: str) -> dict | None:
    """Get MCP server configuration by ID."""
    return MCP_SERVERS.get(server_id)


def get_servers_for_agent(agent_type: str) -> list[dict]:
    """Get all MCP servers that an agent is allowed to use."""
    return [
        server for server in MCP_SERVERS.values()
        if agent_type in server.get('allowed_agents', [])
    ]


def is_action_allowed(server_id: str, action: str, agent_type: str) -> bool:
    """Check if an agent is allowed to perform a specific action on an MCP server."""
    server = MCP_SERVERS.get(server_id)
    if not server:
        return False
    if agent_type not in server.get('allowed_agents', []):
        return False
    if action not in server.get('allowed_actions', []):
        return False
    return True


def get_all_server_ids() -> list[str]:
    return list(MCP_SERVERS.keys())
