import uuid
import logging
from datetime import datetime, timezone

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core import db

logger = logging.getLogger(__name__)

PROJECT_STATUSES = ['planning', 'in_progress', 'review', 'deployed', 'archived']


def _serialize_project(p: dict) -> dict:
    return {
        'id': str(p['_id']),
        'name': p['name'],
        'description': p.get('description', ''),
        'status': p.get('status', 'planning'),
        'tech_stack': p.get('tech_stack', []),
        'owner_id': p['owner_id'],
        'agent_workflow_id': p.get('agent_workflow_id'),
        'created_at': p['created_at'].isoformat(),
        'updated_at': p.get('updated_at', p['created_at']).isoformat(),
    }


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def project_list(request):
    user_id = request.user.id

    if request.method == 'GET':
        projects = list(db.projects().find({'owner_id': user_id}).sort('created_at', -1))
        return Response([_serialize_project(p) for p in projects])

    # POST — create project
    data = request.data
    name = data.get('name', '').strip()
    if not name:
        return Response({'error': 'name is required'}, status=status.HTTP_400_BAD_REQUEST)

    project_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    project = {
        '_id': project_id,
        'name': name,
        'description': data.get('description', ''),
        'status': 'planning',
        'tech_stack': data.get('tech_stack', []),
        'owner_id': user_id,
        'agent_workflow_id': None,
        'created_at': now,
        'updated_at': now,
    }
    db.projects().insert_one(project)
    logger.info(f"Project created: {project_id} by {user_id}")

    return Response(_serialize_project(project), status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def project_detail(request, project_id):
    user_id = request.user.id
    project = db.projects().find_one({'_id': project_id, 'owner_id': user_id})

    if not project:
        return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        # Enrich with stats
        agent_runs_count = db.agent_runs().count_documents({'project_id': project_id})
        files_count = db.project_files().count_documents({'project_id': project_id})
        decisions_count = db.decisions().count_documents({'project_id': project_id})
        data = _serialize_project(project)
        data['stats'] = {
            'agent_runs': agent_runs_count,
            'files': files_count,
            'decisions': decisions_count,
        }
        return Response(data)

    elif request.method == 'PUT':
        updates = {}
        for field in ['name', 'description', 'status', 'tech_stack']:
            if field in request.data:
                updates[field] = request.data[field]
        updates['updated_at'] = datetime.now(timezone.utc)
        db.projects().update_one({'_id': project_id}, {'$set': updates})
        project.update(updates)
        return Response(_serialize_project(project))

    elif request.method == 'DELETE':
        db.projects().delete_one({'_id': project_id})
        db.project_files().delete_many({'project_id': project_id})
        db.agent_runs().delete_many({'project_id': project_id})
        db.memories().delete_many({'project_id': project_id})
        db.decisions().delete_many({'project_id': project_id})
        return Response({'message': 'Project deleted'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def project_files(request, project_id):
    user_id = request.user.id
    project = db.projects().find_one({'_id': project_id, 'owner_id': user_id})
    if not project:
        return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

    files = list(db.project_files().find(
        {'project_id': project_id},
        {'content': 0}  # Exclude content for listing
    ).sort('path', 1))

    return Response([{
        'id': str(f['_id']),
        'path': f['path'],
        'language': f.get('language', 'text'),
        'agent_modified': f.get('agent_modified', False),
        'size': f.get('size', 0),
        'updated_at': f.get('updated_at', '').isoformat() if f.get('updated_at') else None,
    } for f in files])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def project_file_content(request, project_id, file_path):
    user_id = request.user.id
    project = db.projects().find_one({'_id': project_id, 'owner_id': user_id})
    if not project:
        return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

    file = db.project_files().find_one({'project_id': project_id, 'path': file_path})
    if not file:
        return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

    return Response({
        'path': file['path'],
        'content': file.get('content', ''),
        'language': file.get('language', 'text'),
        'agent_modified': file.get('agent_modified', False),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def project_decisions(request, project_id):
    user_id = request.user.id
    project = db.projects().find_one({'_id': project_id, 'owner_id': user_id})
    if not project:
        return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

    decisions = list(db.decisions().find(
        {'project_id': project_id}
    ).sort('created_at', -1).limit(50))

    return Response([{
        'id': str(d['_id']),
        'title': d['title'],
        'rationale': d['rationale'],
        'alternatives_considered': d.get('alternatives_considered', []),
        'decided_by_agent': d.get('decided_by_agent', 'system'),
        'tags': d.get('tags', []),
        'created_at': d['created_at'].isoformat(),
    } for d in decisions])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def project_tech_debt(request, project_id):
    user_id = request.user.id
    project = db.projects().find_one({'_id': project_id, 'owner_id': user_id})
    if not project:
        return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

    debts = list(db.tech_debt().find(
        {'project_id': project_id, 'resolved_at': None}
    ).sort('severity', -1))

    return Response([{
        'id': str(d['_id']),
        'description': d['description'],
        'severity': d['severity'],
        'file_path': d.get('file_path', ''),
        'created_at': d['created_at'].isoformat(),
    } for d in debts])
