import logging
import time
from celery import shared_task, chain
from core import db

logger = logging.getLogger(__name__)

# ─── Agent class registry ───────────────────────────────────────────────────
AGENT_CLASSES = {
    'planner':       'core.agents.planner_agent.PlannerAgent',
    'architect':     'core.agents.architect_agent.ArchitectAgent',
    'backend_dev':   'core.agents.backend_agent.BackendAgent',
    'frontend':      'core.agents.frontend_agent.FrontendAgent',
    'reviewer':      'core.agents.reviewer_agent.ReviewerAgent',
    'testing':       'core.agents.testing_agent.TestingAgent',
    'documentation': 'core.agents.documentation_agent.DocumentationAgent',
    'memory':        'core.agents.memory_agent.MemoryAgent',
}


def _notify_ws(project_id: str, message: dict):
    """Push a message to the project's WebSocket room group."""
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'project_{project_id}',
                {'type': 'agent_event', 'message': message}
            )
    except Exception as e:
        logger.warning(f"WebSocket notification failed: {e}")


@shared_task(bind=True, queue='default', max_retries=3)
def run_workflow_async(self, project_id: str, workflow_id: str, input_data: str):
    """
    Main entry point for orchestrating a multi-agent workflow.
    Chains: planner → architect → backend_dev → frontend → reviewer → testing → documentation → memory
    """
    logger.info(f"Starting workflow {workflow_id} for project {project_id}")
    db.agent_workflows().update_one(
        {'_id': workflow_id},
        {'$set': {'status': 'running', 'current_step': 'planner'}}
    )

    _notify_ws(project_id, {
        'type': 'workflow_start',
        'workflow_id': workflow_id,
        'message': 'Full workflow started. Agents will run in sequence.',
    })

    # Build the full pipeline chain
    # Each step passes its output as input_data to the next (via .si — immutable signatures — we don't chain data)
    workflow_chain = chain(
        run_single_agent_async.si(project_id, workflow_id, 'planner',        input_data).set(queue='planner'),
        run_single_agent_async.si(project_id, workflow_id, 'architect',      '').set(queue='architect'),
        run_single_agent_async.si(project_id, workflow_id, 'backend_dev',    '').set(queue='backend_dev'),
        run_single_agent_async.si(project_id, workflow_id, 'frontend',       '').set(queue='frontend'),
        run_single_agent_async.si(project_id, workflow_id, 'reviewer',       '').set(queue='reviewer'),
        run_single_agent_async.si(project_id, workflow_id, 'testing',        '').set(queue='testing'),
        run_single_agent_async.si(project_id, workflow_id, 'documentation',  '').set(queue='documentation'),
        run_single_agent_async.si(project_id, workflow_id, 'memory',         '').set(queue='memory'),
    )

    workflow_chain.apply_async()


@shared_task(bind=True, max_retries=3)
def run_single_agent_async(self, project_id: str, run_id: str, agent_type: str, input_data: str):
    """
    Executes a single LangGraph agent task. Routed to its dedicated Celery queue.
    Sends real-time progress events via WebSocket before and after execution.
    """
    logger.info(f"Starting agent '{agent_type}' | run={run_id} | project={project_id}")
    start_time = time.monotonic()

    db.agent_runs().update_one(
        {'_id': run_id},
        {'$set': {'status': 'running', 'started_at': __import__('datetime').datetime.now(__import__('datetime').timezone.utc)}}
    )

    # Notify frontend that this agent has started
    _notify_ws(project_id, {
        'type': 'agent_start',
        'agent': agent_type,
        'run_id': run_id,
        'message': f'{agent_type.replace("_", " ").title()} agent started...',
    })

    output = ''
    tokens_used = 0
    cost = 0.0
    error_msg = None

    if agent_type in AGENT_CLASSES:
        import importlib
        module_path, class_name = AGENT_CLASSES[agent_type].rsplit('.', 1)
        try:
            module = importlib.import_module(module_path)
            AgentClass = getattr(module, class_name)
            agent = AgentClass(project_id, run_id)
            output = agent.run(input_data or f"Continue the project build workflow as the {agent_type} agent.")

            # Extract token usage from LangChain callbacks if available
            # (LangChain attaches usage_metadata to the last message when supported)
            try:
                last_msg = agent.graph.get_state(None) if hasattr(agent.graph, 'get_state') else None
            except Exception:
                last_msg = None

        except Exception as e:
            logger.error(f"Agent '{agent_type}' failed: {e}", exc_info=True)
            output = f"Agent encountered an error: {str(e)}"
            error_msg = str(e)
    else:
        output = f"Unknown agent type: {agent_type}"
        error_msg = output

    duration = round(time.monotonic() - start_time, 2)
    final_status = 'failed' if error_msg else 'completed'

    db.agent_runs().update_one(
        {'_id': run_id},
        {'$set': {
            'status': final_status,
            'output': output,
            'error': error_msg,
            'tokens_used': tokens_used,
            'cost': cost,
            'duration': duration,
        }}
    )

    # Notify frontend of completion (or failure)
    _notify_ws(project_id, {
        'type': 'agent_complete' if not error_msg else 'agent_error',
        'agent': agent_type,
        'run_id': run_id,
        'output': output,
        'duration': duration,
        'tokens_used': tokens_used,
    })

    return output

