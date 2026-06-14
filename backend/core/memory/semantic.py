"""
Semantic Memory (Vector Search)
Supports two providers:
  - 'local': sentence-transformers (no API key, bundled in requirements)
  - 'openai': OpenAI text-embedding-3-small (requires OPENAI_API_KEY)
Falls back to MongoDB text-index search if embeddings fail.
"""
import logging
from django.conf import settings
from core import db

logger = logging.getLogger(__name__)

# ─── Lazy provider initialisation ────────────────────────────────────────────

_model_cache = {}   # Local ST model cache (expensive to load, reuse)


def _get_local_model():
    """Load and cache the SentenceTransformers all-MiniLM-L6-v2 model."""
    if 'local' not in _model_cache:
        try:
            from sentence_transformers import SentenceTransformer
            _model_cache['local'] = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ Local sentence-transformers model loaded (all-MiniLM-L6-v2)")
        except Exception as e:
            logger.warning(f"sentence-transformers unavailable: {e}")
            _model_cache['local'] = None
    return _model_cache['local']


class SemanticMemory:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.provider = getattr(settings, 'EMBEDDING_PROVIDER', 'local')
        self._openai_embeddings = None

        if self.provider == 'openai':
            openai_key = getattr(settings, 'OPENAI_API_KEY', '')
            if openai_key:
                try:
                    from langchain_openai import OpenAIEmbeddings
                    self._openai_embeddings = OpenAIEmbeddings(
                        model=getattr(settings, 'EMBEDDING_MODEL', 'text-embedding-3-small'),
                        api_key=openai_key,
                    )
                    logger.info("✅ OpenAI embeddings provider initialised")
                except Exception as e:
                    logger.warning(f"OpenAI embeddings failed to init, falling back to local: {e}")
                    self.provider = 'local'
            else:
                logger.warning("OPENAI_API_KEY not set — falling back to local embeddings")
                self.provider = 'local'

    # ─── Embedding generation ─────────────────────────────────────────────────

    def generate_embedding(self, text: str) -> list[float] | None:
        """Generate a vector embedding for a text string."""
        try:
            if self.provider == 'openai' and self._openai_embeddings:
                return self._openai_embeddings.embed_query(text)

            # Local sentence-transformers fallback
            model = _get_local_model()
            if model:
                embedding = model.encode(text, normalize_embeddings=True)
                return embedding.tolist()
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
        return None

    # ─── Vector Search ────────────────────────────────────────────────────────

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Perform a semantic similarity search over project memories.
        Tries MongoDB Atlas $vectorSearch first, then falls back to text search.
        """
        query_vector = self.generate_embedding(query)
        if not query_vector:
            logger.info("Embeddings unavailable — returning empty semantic results")
            return []

        # Try Atlas Vector Search (requires M10+ cluster with vector index)
        try:
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
                        "_id": 1, "type": 1, "title": 1, "content": 1,
                        "created_at": 1,
                        "score": {"$meta": "vectorSearchScore"}
                    }
                }
            ]
            results = list(db.memories().aggregate(pipeline))
            if results:
                for r in results:
                    r['id'] = str(r.pop('_id'))
                    if 'created_at' in r:
                        r['created_at'] = r['created_at'].isoformat()
                return results
        except Exception as e:
            logger.info(f"Atlas Vector Search unavailable ({e}) — falling back to cosine similarity")

        # Cosine similarity fallback: compare against stored embeddings in memory
        return self._cosine_fallback(query_vector, top_k)

    def _cosine_fallback(self, query_vector: list[float], top_k: int) -> list[dict]:
        """
        In-memory cosine similarity search as a fallback when Atlas is unavailable.
        Loads all embeddings for the project and computes similarity in Python.
        Only viable for small projects (< 10k memories).
        """
        try:
            import numpy as np
            query_arr = np.array(query_vector)
            docs = list(db.memories().find(
                {'project_id': self.project_id, 'embedding': {'$exists': True}},
                {'embedding': 1, 'type': 1, 'title': 1, 'content': 1, 'created_at': 1}
            ))
            if not docs:
                return []

            scored = []
            for doc in docs:
                emb = np.array(doc['embedding'])
                score = float(np.dot(query_arr, emb) / (np.linalg.norm(query_arr) * np.linalg.norm(emb) + 1e-9))
                scored.append((score, doc))

            scored.sort(key=lambda x: x[0], reverse=True)
            return [{
                'id': str(doc['_id']),
                'type': doc['type'],
                'title': doc.get('title'),
                'content': doc['content'],
                'score': score,
                'created_at': doc['created_at'].isoformat(),
            } for score, doc in scored[:top_k]]
        except Exception as e:
            logger.error(f"Cosine fallback failed: {e}")
            return []

    def save_with_embedding(self, memory_doc: dict) -> dict:
        """
        Generate and attach an embedding vector to a memory document before saving.
        Called by MemoryMCPServer when embeddings are available.
        """
        text = f"{memory_doc.get('title', '')} {memory_doc.get('content', '')}".strip()
        embedding = self.generate_embedding(text)
        if embedding:
            memory_doc['embedding'] = embedding
        return memory_doc
