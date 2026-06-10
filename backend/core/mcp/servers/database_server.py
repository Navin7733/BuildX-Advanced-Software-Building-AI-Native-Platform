"""
BuildX Custom Database MCP Server
Allows backend and testing agents to validate schemas, query data,
and seed test fixtures in an isolated manner.
Runs in-process (transport="python_module").
"""
import logging
from core import db

logger = logging.getLogger(__name__)


class DatabaseMCPServer:
    def __init__(self, project_id: str):
        self.project_id = project_id
        # In a real implementation, this would connect to a dynamically
        # provisioned per-project database or collection prefix.
        # For MVP, we'll prefix collections with project_id.
        self.prefix = f"proj_{project_id}_"

    def get_collection(self, name: str):
        return db.get_collection(f"{self.prefix}{name}")

    def validate_schema(self, collection_name: str, schema: dict) -> dict:
        """
        Validate a JSON schema against MongoDB.
        In MongoDB, we can set schema validation rules on collections.
        """
        try:
            db_conn = db.get_db()
            col_name = f"{self.prefix}{collection_name}"
            
            # Check if collection exists
            if col_name not in db_conn.list_collection_names():
                # Create collection with validator
                db_conn.create_collection(col_name, validator={'$jsonSchema': schema})
                return {'status': 'success', 'message': 'Collection created with schema validation'}
            else:
                # Update existing validator
                db_conn.command('collMod', col_name, validator={'$jsonSchema': schema})
                return {'status': 'success', 'message': 'Schema validation updated'}
        except Exception as e:
            logger.error(f"Schema validation error: {e}")
            return {'status': 'error', 'message': str(e)}

    def list_collections(self) -> list[str]:
        """List all collections for this project."""
        db_conn = db.get_db()
        all_cols = db_conn.list_collection_names()
        return [c.replace(self.prefix, '') for c in all_cols if c.startswith(self.prefix)]

    def run_query(self, collection_name: str, query: dict, limit: int = 10) -> list[dict]:
        """Run a sandboxed read-only query against a project collection."""
        col = self.get_collection(collection_name)
        try:
            docs = list(col.find(query).limit(limit))
            # Convert ObjectId to string for JSON serialization
            for d in docs:
                if '_id' in d:
                    d['_id'] = str(d['_id'])
            return docs
        except Exception as e:
            return [{'error': str(e)}]

    def seed_test_data(self, collection_name: str, documents: list[dict]) -> dict:
        """Insert test fixtures into a project collection."""
        if not documents:
            return {'status': 'error', 'message': 'No documents provided'}
            
        try:
            col = self.get_collection(collection_name)
            result = col.insert_many(documents)
            return {
                'status': 'success', 
                'inserted_count': len(result.inserted_ids)
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
