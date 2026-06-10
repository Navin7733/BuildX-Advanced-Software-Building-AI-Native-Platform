"""
Semantic Memory (Vector Search)
Generates embeddings using OpenAI and searches MongoDB Atlas Vector Search.
"""
import logging
from django.conf import settings
from langchain_openai import OpenAIEmbeddings

from core import db

logger = logging.getLogger(__name__)

class SemanticMemory:
    def __init__(self, project_id: str):
        self.project_id = project_id
        # We need an OpenAI API key for embeddings, even if using OpenRouter for LLM.
        # If not provided, we fall back to text search in the MCP server.
        self.has_embeddings = bool(settings.OPENROUTER_API_KEY)  # Assuming we use same key if it's an OpenAI key
        if self.has_embeddings:
            try:
                self.embeddings = OpenAIEmbeddings(
                    model=settings.EMBEDDING_MODEL,
                    api_key=settings.OPENROUTER_API_KEY, # This might fail if OpenRouter doesn't support embeddings endpoint perfectly
                    base_url=settings.OPENROUTER_BASE_URL
                )
            except Exception as e:
                logger.warning(f"Failed to initialize embeddings: {e}")
                self.has_embeddings = False

    def generate_embedding(self, text: str) -> list[float] | None:
        if not self.has_embeddings:
            return None
        try:
            return self.embeddings.embed_query(text)
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return None

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Perform vector search using MongoDB Atlas.
        Requires a vector index named 'vector_index' on the 'memories' collection.
        """
        if not self.has_embeddings:
            logger.info("Embeddings disabled, returning empty semantic search results.")
            return []

        query_vector = self.generate_embedding(query)
        if not query_vector:
            return []

        # Atlas Vector Search pipeline
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embedding",
                    "queryVector": query_vector,
                    "numCandidates": top_k * 10,
                    "limit": top_k,
                    "filter": {"project_id": {"$eq": self.project_id}}
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "type": 1,
                    "title": 1,
                    "content": 1,
                    "created_at": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]

        try:
            results = list(db.memories().aggregate(pipeline))
            for r in results:
                r['id'] = str(r['_id'])
                del r['_id']
                if 'created_at' in r:
                    r['created_at'] = r['created_at'].isoformat()
            return results
        except Exception as e:
            logger.error(f"Atlas Vector Search failed: {e}. Ensure cluster tier is M10+ and index exists.")
            return []
