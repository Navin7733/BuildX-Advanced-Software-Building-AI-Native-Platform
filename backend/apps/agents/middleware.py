from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from apps.accounts.auth import MongoJWTAuthentication

class JWTAuthMiddleware:
    """
    WebSocket middleware that authenticates the user via JWT token
    passed in the query string: ?token=<jwt>
    """
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode('utf-8')
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]

        if token:
            user = await self.get_user_from_token(token)
            if user:
                scope['user'] = user

        return await self.inner(scope, receive, send)

    @database_sync_to_async
    def get_user_from_token(self, token):
        try:
            auth = MongoJWTAuthentication()
            validated_token = auth.get_validated_token(token)
            user = auth.get_user(validated_token)
            return user
        except (InvalidToken, TokenError):
            return None
