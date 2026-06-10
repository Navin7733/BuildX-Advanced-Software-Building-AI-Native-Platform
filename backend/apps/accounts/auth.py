"""
Custom JWT authentication that reads user_id from MongoDB.
Used by both REST views and WebSocket middleware.
"""
import logging
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.exceptions import AuthenticationFailed
from core import db

logger = logging.getLogger(__name__)


class MongoJWTAuthentication(JWTAuthentication):
    """
    Extends JWTAuthentication to load the user from MongoDB
    instead of the Django ORM User model.
    """

    def get_user(self, validated_token):
        try:
            user_id = validated_token.get('user_id')
            if not user_id:
                raise InvalidToken('Token contains no user_id')

            user = db.users().find_one({'_id': user_id})
            if not user:
                raise AuthenticationFailed('User not found')

            # Return a simple object that DRF expects
            return MongoUser(user)
        except (InvalidToken, TokenError) as e:
            raise AuthenticationFailed(str(e))


class MongoUser:
    """
    Lightweight user object that wraps a MongoDB user document.
    DRF only needs is_authenticated and a few properties.
    """

    def __init__(self, doc: dict):
        self._doc = doc
        self.id = str(doc['_id'])
        self.email = doc['email']
        self.name = doc['name']
        self.role = doc.get('role', 'developer')
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False

    def __str__(self):
        return self.email
