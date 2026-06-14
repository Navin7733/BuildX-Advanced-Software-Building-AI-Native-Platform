"""
BuildX Custom Memory MCP Server
Provides memory and decision storage/retrieval for LangGraph agents.
Runs in-process (transport="python_module").
"""
import uuid
from datetime import datetime, timezone
import logging

from core import db

logger = logging.getLogger(__name__)


class MemoryMCPServer:
    def __init__(self, project_id: str):
        self.project_id = project_id

    def save_decision(self, title: str, rationale: str, alternatives: list[str] = None, agent: str = None, tags: list[str] = None) -> dict:
        """Save an architectural or engineering decision."""
        doc = {
            '_id': str(uuid.uuid4()),
            'project_id': self.project_id,
            'title': title,
            'rationale': rationale,
            'alternatives_considered': alternatives or [],
            'decided_by_agent': agent,
            'tags': tags or [],
            'created_at': datetime.now(timezone.utc),
        }
        db.decisions().insert_one(doc)
        
        # Also store it in generic memories for vector search
        self.save_memory(
            type="decision",
            content=f"Decision: {title}\nRationale: {rationale}",
            title=title,
            tags=tags
        )
        
        return {'status': 'success', 'decision_id': doc['_id']}

    def get_decisions(self, limit: int = 20) -> list[dict]:
        """Retrieve recent decisions for the project."""
        docs = db.decisions().find({'project_id': self.project_id}).sort('created_at', -1).limit(limit)
        return [{
            'id': str(d['_id']),
            'title': d['title'],
            'rationale': d['rationale'],
            'tags': d.get('tags', []),
            'created_at': d['created_at'].isoformat()
        } for d in docs]

    def save_memory(self, type: str, content: str, title: str = None, tags: list[str] = None) -> dict:
        """Save a generic project memory (bug, context, preference)."""
        memory_id = str(uuid.uuid4())
        doc = {
            '_id': memory_id,
            'project_id': self.project_id,
            'type': type,
            'title': title,
            'content': content,
            'tags': tags or [],
            'created_at': datetime.now(timezone.utc),
        }
        
        # In a real implementation, we would generate vector embeddings here
        # via core.memory.semantic before inserting.
        # For MVP skeleton, we just insert.
        db.memories().insert_one(doc)
        return {'status': 'success', 'memory_id': memory_id}

    def search_memories(self, query: str, top_k: int = 5) -> list[dict]:
        """Text/semantic search over project memories."""
        results = []
        try:
            # Try text-index search first
            results = list(db.memories().find({
                'project_id': self.project_id,
                '$text': {'$search': query}
            }, {'score': {'$meta': 'textScore'}}).sort([('score', {'$meta': 'textScore'})]).limit(top_k))
        except Exception:
            pass

        if not results:
            # Fallback: simple regex search across title and content
            import re
            pattern = re.compile(re.escape(query), re.IGNORECASE)
            results = list(db.memories().find({
                'project_id': self.project_id,
                '$or': [{'title': pattern}, {'content': pattern}]
            }).limit(top_k))

        if not results:
            # Last resort: return the most recent memories
            results = list(
                db.memories()
                .find({'project_id': self.project_id})
                .sort('created_at', -1)
                .limit(top_k)
            )

        return [{
            'id': str(d['_id']),
            'type': d['type'],
            'title': d.get('title'),
            'content': d['content'],
            'created_at': d['created_at'].isoformat(),
        } for d in results]

    def search_similar(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Vector-similarity search over project memories.
        Falls back to search_memories if Atlas vector search isn't configured.
        """
        try:
            from core.memory.semantic import SemanticMemory
            semantic = SemanticMemory(self.project_id)
            vector_results = semantic.search(query, top_k=top_k)
            if vector_results:
                return vector_results
        except Exception as e:
            logger.warning(f"Vector search unavailable, falling back to text search: {e}")

        return self.search_memories(query, top_k=top_k)
