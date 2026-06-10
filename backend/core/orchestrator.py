import logging
from celery import shared_task
from core import db

logger = logging.getLogger(__name__)


@shared_task(bind=True, queue='default', max_retries=3)
def run_workflow_async(self, project_id: str, workflow_id: str, input_data: str):
    """
    Main entry point for orchestrating a multi-agent workflow.
    Triggers the planner, which emits an event to trigger the architect, etc.
    For MVP, we can sequentially chain Celery tasks or use chords.
    """
    logger.info(f"Starting workflow {workflow_id} for project {project_id}")
    db.agent_workflows().update_one(
        {'_id': workflow_id},
        {'$set': {'status': 'running', 'current_step': 'planner'}}
    )

    # Chain the agent runs
    from celery import chain
    workflow_chain = chain(
        run_single_agent_async.si(project_id, workflow_id, 'planner', input_data).set(queue='planner'),
        run_single_agent_async.si(project_id, workflow_id, 'architect', '').set(queue='architect'),
        # Note: In a full implementation, frontend and backend could be a group() running in parallel
        run_single_agent_async.si(project_id, workflow_id, 'backend_dev', '').set(queue='backend_dev'),
        run_single_agent_async.si(project_id, workflow_id, 'frontend', '').set(queue='frontend'),
    )
    
    workflow_chain.apply_async()


@shared_task(bind=True, max_retries=3)
def run_single_agent_async(self, project_id: str, run_id: str, agent_type: str, input_data: str):
    """
    Executes a specific LangGraph agent.
    This task is routed to the specific Celery queue based on `agent_type`.
    """
    logger.info(f"Starting agent {agent_type} run {run_id} for project {project_id}")
    
    db.agent_runs().update_one(
        {'_id': run_id},
        {'$set': {'status': 'running'}}
    )

    # Map agent_type to agent class
    agent_classes = {
        'planner': 'core.agents.planner_agent.PlannerAgent',
        'architect': 'core.agents.architect_agent.ArchitectAgent',
        'backend_dev': 'core.agents.backend_agent.BackendAgent',
        'frontend': 'core.agents.frontend_agent.FrontendAgent',
        'memory': 'core.agents.memory_agent.MemoryAgent',
    }

    output = ""
    if agent_type in agent_classes:
        import importlib
        module_path, class_name = agent_classes[agent_type].rsplit('.', 1)
        module = importlib.import_module(module_path)
        AgentClass = getattr(module, class_name)
        
        try:
            agent = AgentClass(project_id, run_id)
            output = agent.run(input_data)
        except Exception as e:
            logger.error(f"Agent {agent_type} run failed: {e}")
            output = f"Error during execution: {e}"
    else:
        output = f"Unknown agent type: {agent_type}"

    db.agent_runs().update_one(
        {'_id': run_id},
        {'$set': {
            'status': 'completed',
            'output': output,
            'tokens_used': 100,
            'cost': 0.001,
            'duration': 5,
        }}
    )

    # Notify WebSocket
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer
    channel_layer = get_channel_layer()
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            f'project_{project_id}',
            {
                'type': 'agent_event',
                'message': {
                    'type': 'agent_complete',
                    'agent': agent_type,
                    'output': output,
                }
            }
        )

    return output
