import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core import db

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_memories(request, project_id):
    """List all memories for a project, filtered by type optionally."""
    user_id = request.user.id
    project = db.projects().find_one({'_id': project_id, 'owner_id': user_id})
    if not project:
        return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

    memory_type = request.query_params.get('type')
    query = {'project_id': project_id}
    if memory_type:
        query['type'] = memory_type

    # Exclude embeddings from the API response
    memories = list(db.memories().find(query, {'embedding': 0}).sort('created_at', -1))
    
    return Response([{
        'id': str(m['_id']),
        'type': m['type'],
        'title': m.get('title', ''),
        'content': m.get('content', ''),
        'tags': m.get('tags', []),
        'metadata': m.get('metadata', {}),
        'created_at': m['created_at'].isoformat(),
    } for m in memories])


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def search_memories(request, project_id):
    """Semantic search over memories using vector search."""
    user_id = request.user.id
    project = db.projects().find_one({'_id': project_id, 'owner_id': user_id})
    if not project:
        return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

    query = request.data.get('query')
    if not query:
        return Response({'error': 'query is required'}, status=status.HTTP_400_BAD_REQUEST)

    # Note: Semantic search will use MongoDB Atlas Vector Search ($vectorSearch).
    # For MVP, we'll return a stub or fallback to text search if Atlas isn't fully configured yet.
    # The actual semantic search logic lives in `core.memory.semantic`.
    from core.memory.semantic import SemanticMemory
    semantic = SemanticMemory(project_id)
    results = semantic.search(query, top_k=5)

    return Response(results)
