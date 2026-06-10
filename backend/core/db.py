"""
MongoDB connection singleton.
All apps use db.get_db() to get the pymongo database instance.
"""
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from django.conf import settings

logger = logging.getLogger(__name__)

_client = None
_db = None


def get_client():
    global _client
    if _client is None:
        _client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=5000)
        try:
            _client.admin.command('ping')
            logger.info("✅ MongoDB connected successfully")
        except ConnectionFailure as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            raise
    return _client


def get_db():
    global _db
    if _db is None:
        _db = get_client()[settings.MONGODB_DB_NAME]
    return _db


def get_collection(name: str):
    return get_db()[name]


# ─── Collection accessors ─────────────────────────────────────
def users():
    return get_collection('users')

def projects():
    return get_collection('projects')

def project_files():
    return get_collection('project_files')

def agent_runs():
    return get_collection('agent_runs')

def agent_workflows():
    return get_collection('agent_workflows')

def memories():
    return get_collection('memories')

def decisions():
    return get_collection('decisions')

def tech_debt():
    return get_collection('tech_debt')

def knowledge_nodes():
    return get_collection('knowledge_nodes')

def knowledge_edges():
    return get_collection('knowledge_edges')

def audit_logs():
    return get_collection('audit_logs')


def create_indexes():
    """Create all MongoDB indexes on startup."""
    db = get_db()

    # Users
    db.users.create_index('email', unique=True)

    # Projects
    db.projects.create_index('owner_id')
    db.projects.create_index('created_at')

    # Project files
    db.project_files.create_index([('project_id', 1), ('path', 1)], unique=True)

    # Agent runs
    db.agent_runs.create_index([('project_id', 1), ('created_at', -1)])
    db.agent_runs.create_index('status')

    # Agent workflows
    db.agent_workflows.create_index('project_id')

    # Memories
    db.memories.create_index([('project_id', 1), ('type', 1)])
    db.memories.create_index([('project_id', 1), ('created_at', -1)])

    # Decisions
    db.decisions.create_index([('project_id', 1), ('created_at', -1)])

    # Tech debt
    db.tech_debt.create_index([('project_id', 1), ('severity', 1)])

    # Knowledge graph
    db.knowledge_nodes.create_index([('project_id', 1), ('type', 1)])
    db.knowledge_edges.create_index([('project_id', 1), ('source_id', 1)])

    # Audit logs
    db.audit_logs.create_index([('user_id', 1), ('timestamp', -1)])

    logger.info("✅ MongoDB indexes created")
