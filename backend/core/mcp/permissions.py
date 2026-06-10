"""
MCP Permission Layer
Validates agent tool requests against the registry allowlists
and writes every call to the MongoDB audit log.
"""
import uuid
import logging
from datetime import datetime, timezone

from core import db
from .registry import is_action_allowed, get_server_config

logger = logging.getLogger(__name__)


class MCPPermissionDenied(Exception):
    pass


class MCPPermissions:
    def __init__(self, agent_type: str, project_id: str, run_id: str):
        self.agent_type = agent_type
        self.project_id = project_id
        self.run_id = run_id
        self._call_counts: dict[str, int] = {}

    def check_and_audit(self, server_id: str, action: str, args: dict) -> None:
        """
        Validates the call is permitted, checks rate limits,
        and writes an audit log entry. Raises MCPPermissionDenied on failure.
        """
        # 1. Registry permission check
        if not is_action_allowed(server_id, action, self.agent_type):
            msg = (f"Agent '{self.agent_type}' is NOT allowed to call "
                   f"'{action}' on MCP server '{server_id}'")
            logger.warning(f"[MCP DENIED] {msg}")
            self._write_audit(server_id, action, args, denied=True, reason=msg)
            raise MCPPermissionDenied(msg)

        # 2. Rate limit check
        server = get_server_config(server_id)
        rate_limit = server.get('rate_limit_per_run', 100)
        key = f"{server_id}"
        self._call_counts[key] = self._call_counts.get(key, 0) + 1
        if self._call_counts[key] > rate_limit:
            msg = (f"Rate limit exceeded: agent '{self.agent_type}' has called "
                   f"'{server_id}' {self._call_counts[key]} times (limit: {rate_limit})")
            logger.warning(f"[MCP RATE LIMIT] {msg}")
            self._write_audit(server_id, action, args, denied=True, reason=msg)
            raise MCPPermissionDenied(msg)

        # 3. Human approval check
        if server.get('requires_human_approval'):
            logger.info(f"[MCP HUMAN APPROVAL] {server_id}.{action} flagged for approval")

        # 4. Write allowed audit entry
        self._write_audit(server_id, action, args, denied=False, reason=None)
        logger.debug(f"[MCP ALLOWED] {self.agent_type} → {server_id}.{action}")

    def _write_audit(self, server_id: str, action: str, args: dict,
                     denied: bool, reason: str | None):
        """Write MCP call to audit_logs collection."""
        try:
            db.audit_logs().insert_one({
                '_id': str(uuid.uuid4()),
                'type': 'mcp_call',
                'project_id': self.project_id,
                'agent_run_id': self.run_id,
                'agent_type': self.agent_type,
                'mcp_server': server_id,
                'mcp_action': action,
                'args_summary': {k: str(v)[:200] for k, v in args.items()},
                'denied': denied,
                'denial_reason': reason,
                'timestamp': datetime.now(timezone.utc),
            })
        except Exception as e:
            logger.error(f"Failed to write MCP audit log: {e}")
