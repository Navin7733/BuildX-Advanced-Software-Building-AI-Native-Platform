"""
MCP Client
Connects to MCP servers and executes tool calls.
Supports both Python module (in-process) and stdio (subprocess) transports.
"""
import asyncio
import json
import logging
import subprocess
from typing import Any

from .registry import get_server_config
from .permissions import MCPPermissions, MCPPermissionDenied

logger = logging.getLogger(__name__)


class MCPClient:
    """
    Unified MCP client that dispatches tool calls to the correct server.
    Enforces permissions before every call.
    """

    def __init__(self, agent_type: str, project_id: str, run_id: str):
        self.agent_type = agent_type
        self.project_id = project_id
        self.run_id = run_id
        self.permissions = MCPPermissions(agent_type, project_id, run_id)

    def call(self, server_id: str, action: str, **kwargs) -> dict[str, Any]:
        """
        Execute an MCP tool call with full permission check + audit.

        Returns: dict with keys 'success', 'result', 'error'
        """
        try:
            self.permissions.check_and_audit(server_id, action, kwargs)
        except MCPPermissionDenied as e:
            return {'success': False, 'result': None, 'error': str(e)}

        server = get_server_config(server_id)
        if not server:
            return {'success': False, 'result': None, 'error': f"Unknown MCP server: {server_id}"}

        transport = server.get('transport', 'stdio')

        try:
            if transport == 'python_module':
                return self._call_python_module(server, action, kwargs)
            elif transport == 'stdio':
                return self._call_stdio(server, action, kwargs)
            else:
                return {'success': False, 'result': None, 'error': f"Unknown transport: {transport}"}
        except Exception as e:
            logger.error(f"MCP call failed [{server_id}.{action}]: {e}")
            return {'success': False, 'result': None, 'error': str(e)}

    def _call_python_module(self, server: dict, action: str, args: dict) -> dict:
        """Call an in-process Python MCP server."""
        module_path = server['module']
        # Dynamically import and call the server function
        parts = module_path.rsplit('.', 1)
        if len(parts) != 2:
            return {'success': False, 'result': None, 'error': 'Invalid module path'}

        import importlib
        module = importlib.import_module(parts[0])
        server_class = getattr(module, parts[1].split('_')[0].capitalize() + 'MCPServer', None)

        if server_class is None:
            # Try function-based approach
            func = getattr(module, action, None)
            if func:
                result = func(**args)
                return {'success': True, 'result': result, 'error': None}
            return {'success': False, 'result': None, 'error': f"No handler for action: {action}"}

        instance = server_class(self.project_id)
        func = getattr(instance, action, None)
        if not func:
            return {'success': False, 'result': None, 'error': f"Action not found: {action}"}

        result = func(**args)
        return {'success': True, 'result': result, 'error': None}

    def _call_stdio(self, server: dict, action: str, args: dict) -> dict:
        """
        Call a stdio-based MCP server (e.g. npx @modelcontextprotocol/server-filesystem).
        Sends a JSON-RPC request and reads the response.
        """
        import os
        import shutil

        command = server.get('command', 'npx')
        cmd_args = server.get('args', [])
        env_extras = server.get('env_extras', {})

        # Attach filesystem root for filesystem server
        if server['id'] == 'filesystem':
            cmd_args = cmd_args + [self._get_project_path()]

        env = {**os.environ, **{k: v for k, v in env_extras.items() if v}}

        # Check if command exists
        if not shutil.which(command):
            return {'success': False, 'result': None,
                    'error': f"Command not found: {command}. Install Node.js/npx."}

        request = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': f'tools/{action}',
            'params': args,
        }

        try:
            proc = subprocess.run(
                [command] + cmd_args,
                input=json.dumps(request),
                capture_output=True,
                text=True,
                timeout=30,
                env=env,
            )

            if proc.returncode != 0:
                return {'success': False, 'result': None,
                        'error': f"MCP server error: {proc.stderr[:500]}"}

            response = json.loads(proc.stdout)
            if 'error' in response:
                return {'success': False, 'result': None, 'error': response['error']}

            return {'success': True, 'result': response.get('result'), 'error': None}

        except subprocess.TimeoutExpired:
            return {'success': False, 'result': None, 'error': 'MCP server timeout (30s)'}
        except json.JSONDecodeError:
            return {'success': False, 'result': None, 'error': 'Invalid JSON from MCP server'}

    def _get_project_path(self) -> str:
        from django.conf import settings
        import os
        return os.path.join(settings.MCP_FILESYSTEM_ROOT, self.project_id)
