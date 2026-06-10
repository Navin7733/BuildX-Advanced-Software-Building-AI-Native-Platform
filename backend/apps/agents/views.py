import uuid
import logging
from datetime import datetime, timezone

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core import db
from core.orchestrator import run_workflow_async, run_single_agent_async

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_workflow(request, project_id):
    """Trigger the full LangGraph workflow for a project."""
    user_id = request.user.id
    project = db.projects().find_one({'_id': project_id, 'owner_id': user_id})
    if not project:
        return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

    input_data = request.data.get('input')
    if not input_data:
        return Response({'error': 'input is required'}, status=status.HTTP_400_BAD_REQUEST)

    workflow_id = str(uuid.uuid4())
    db.agent_workflows().insert_one({
        '_id': workflow_id,
        'project_id': project_id,
        'status': 'queued',
        'current_step': 'planner',
        'created_at': datetime.now(timezone.utc),
    })

    # Dispatch to Celery orchestrator
    run_workflow_async.delay(project_id, workflow_id, input_data)

    return Response({'message': 'Workflow started', 'workflow_id': workflow_id}, status=status.HTTP_202_ACCEPTED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_agent(request, project_id, agent_type):
    """Trigger a specific agent run."""
    user_id = request.user.id
    project = db.projects().find_one({'_id': project_id, 'owner_id': user_id})
    if not project:
        return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

    input_data = request.data.get('input', '')

    run_id = str(uuid.uuid4())
    db.agent_runs().insert_one({
        '_id': run_id,
        'project_id': project_id,
        'agent_type': agent_type,
        'status': 'queued',
        'input': input_data,
        'created_at': datetime.now(timezone.utc),
    })

    # Dispatch to specific Celery queue based on agent type
    run_single_agent_async.apply_async(
        args=[project_id, run_id, agent_type, input_data],
        queue=agent_type
    )

    return Response({'message': f'{agent_type} agent queued', 'run_id': run_id}, status=status.HTTP_202_ACCEPTED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_agent_runs(request, project_id):
    """List all agent runs for a project."""
    user_id = request.user.id
    project = db.projects().find_one({'_id': project_id, 'owner_id': user_id})
    if not project:
        return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

    runs = list(db.agent_runs().find({'project_id': project_id}).sort('created_at', -1))
    
    return Response([{
        'id': str(run['_id']),
        'agent_type': run['agent_type'],
        'status': run['status'],
        'tokens_used': run.get('tokens_used', 0),
        'cost': run.get('cost', 0.0),
        'duration': run.get('duration', 0),
        'created_at': run['created_at'].isoformat(),
    } for run in runs])
