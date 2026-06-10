import hashlib
import logging
import uuid
from datetime import datetime, timezone

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from core import db

logger = logging.getLogger(__name__)


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _make_user_response(user: dict) -> dict:
    return {
        'id': str(user['_id']),
        'email': user['email'],
        'name': user['name'],
        'role': user.get('role', 'developer'),
        'created_at': user['created_at'].isoformat(),
    }


def _get_tokens_for_user(user_id: str) -> dict:
    """Create JWT tokens using user_id as the identifier."""
    from rest_framework_simplejwt.tokens import RefreshToken as RT
    # We create a simple token with user_id as claim
    refresh = RT()
    refresh['user_id'] = user_id
    refresh['token_type'] = 'refresh'
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Register a new user."""
    data = request.data
    email = data.get('email', '').strip().lower()
    name = data.get('name', '').strip()
    password = data.get('password', '')

    if not email or not name or not password:
        return Response({'error': 'email, name, and password are required'},
                        status=status.HTTP_400_BAD_REQUEST)

    if len(password) < 8:
        return Response({'error': 'Password must be at least 8 characters'},
                        status=status.HTTP_400_BAD_REQUEST)

    users_col = db.users()

    if users_col.find_one({'email': email}):
        return Response({'error': 'Email already registered'},
                        status=status.HTTP_409_CONFLICT)

    user_id = str(uuid.uuid4())
    user = {
        '_id': user_id,
        'email': email,
        'name': name,
        'password_hash': _hash_password(password),
        'role': 'owner',
        'created_at': datetime.now(timezone.utc),
        'last_login': None,
    }
    users_col.insert_one(user)

    tokens = _get_tokens_for_user(user_id)
    logger.info(f"New user registered: {email}")

    return Response({
        'user': _make_user_response(user),
        'tokens': tokens,
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """Login with email + password, returns JWT tokens."""
    email = request.data.get('email', '').strip().lower()
    password = request.data.get('password', '')

    if not email or not password:
        return Response({'error': 'email and password are required'},
                        status=status.HTTP_400_BAD_REQUEST)

    users_col = db.users()
    user = users_col.find_one({'email': email})

    if not user or user['password_hash'] != _hash_password(password):
        return Response({'error': 'Invalid credentials'},
                        status=status.HTTP_401_UNAUTHORIZED)

    users_col.update_one(
        {'_id': user['_id']},
        {'$set': {'last_login': datetime.now(timezone.utc)}}
    )

    tokens = _get_tokens_for_user(str(user['_id']))
    logger.info(f"User logged in: {email}")

    return Response({
        'user': _make_user_response(user),
        'tokens': tokens,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """Blacklist the refresh token."""
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
    except Exception:
        pass
    return Response({'message': 'Logged out successfully'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    """Return current user profile."""
    user_id = request.auth.payload.get('user_id') if request.auth else None
    if not user_id:
        return Response({'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)

    user = db.users().find_one({'_id': user_id})
    if not user:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    return Response({'user': _make_user_response(user)})


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """Refresh access token."""
    try:
        refresh = RefreshToken(request.data.get('refresh'))
        return Response({'access': str(refresh.access_token)})
    except Exception:
        return Response({'error': 'Invalid or expired refresh token'},
                        status=status.HTTP_401_UNAUTHORIZED)
