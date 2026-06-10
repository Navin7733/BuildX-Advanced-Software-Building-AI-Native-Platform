import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from core import db

logger = logging.getLogger(__name__)


class AgentConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time agent streaming.
    Clients connect to this to receive updates from LangGraph agents running in Celery.
    """
    async def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        self.project_id = self.scope['url_route']['kwargs']['project_id']
        self.room_group_name = f'project_{self.project_id}'

        # TODO: Add ownership/access check for the project using database_sync_to_async

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"WebSocket connected for project: {self.project_id} by user: {user.email}")

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """
        Handle incoming messages from the frontend (e.g. user triggering an agent).
        """
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')

        if message_type == 'run_agent':
            # Delegate to Celery via a view or handler
            agent_type = text_data_json.get('agent')
            input_data = text_data_json.get('input', '')
            logger.info(f"WebSocket requested agent run: {agent_type} with input: {input_data}")
            # Note: The actual dispatching to Celery usually happens via REST API,
            # but we can support it here too. For MVP, we'll just log and maybe echo back.
            await self.send(text_data=json.dumps({
                'type': 'agent_status',
                'agent': agent_type,
                'status': 'queued',
                'message': f'Agent {agent_type} queued.'
            }))

        elif message_type == 'chat':
            # Handle user chat/questions
            pass

    async def agent_event(self, event):
        """
        Receive event from room group (sent by Celery task) and forward to WebSocket.
        """
        # Send message to WebSocket
        await self.send(text_data=json.dumps(event['message']))
