"""
Custom WebSocket authentication middleware for JWT tokens
"""
from urllib.parse import parse_qs
from django.contrib.auth.models import AnonymousUser
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
from jwt import decode as jwt_decode
from django.conf import settings

User = get_user_model()


@database_sync_to_async
def get_user_from_token(token_string):
    """Get user from JWT token"""
    try:
        # Validate token
        UntypedToken(token_string)
        
        # Decode token to get user ID
        # Use SIMPLE_JWT settings for consistency
        from rest_framework_simplejwt.settings import api_settings as jwt_settings
        
        decoded_data = jwt_decode(
            token_string,
            jwt_settings.SIGNING_KEY,
            algorithms=[jwt_settings.ALGORITHM]
        )
        
        # Get user from token
        user_id = decoded_data.get(jwt_settings.USER_ID_CLAIM)
        if user_id:
            return User.objects.get(id=user_id)
    except (TokenError, InvalidToken, User.DoesNotExist):
        pass
    return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Custom middleware to authenticate WebSocket connections using JWT tokens.
    
    Token can be provided in:
    1. Query string: ws://host/ws/assistant/?token=<jwt_token>
    2. Authorization header: Authorization: Bearer <jwt_token>
    """
    
    async def __call__(self, scope, receive, send):
        # Extract token from query string or headers
        token = None
        
        # Check query string (common for WebSocket connections)
        query_string = scope.get('query_string', b'').decode()
        if query_string:
            query_params = parse_qs(query_string)
            token = query_params.get('token', [None])[0]
        
        # If not in query string, check Authorization header
        if not token:
            headers = dict(scope.get('headers', []))
            # Headers are case-insensitive, check both lowercase and original case
            auth_header = None
            for key, value in headers.items():
                if key.lower() == b'authorization':
                    auth_header = value.decode()
                    break
            
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ', 1)[1]
        
        # Authenticate user
        if token:
            scope['user'] = await get_user_from_token(token)
        else:
            scope['user'] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)

