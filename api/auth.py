"""
Authentication and authorization module for MCP Translation Server.
"""
from functools import wraps
from typing import Dict, Optional, List
import jwt
import time
from datetime import datetime, timedelta
import hashlib
import secrets
from flask import request, jsonify, current_app
import redis

class AuthManager:
    """Authentication and authorization manager."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """Initialize auth manager with Redis connection."""
        self.redis = redis.from_url(redis_url)
        self._token_blacklist = set()
    
    def generate_api_key(self, user_id: str, scopes: List[str], expiry_days: int = 365) -> str:
        """Generate a new API key for a user."""
        api_key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Store API key metadata
        key_data = {
            'user_id': user_id,
            'scopes': scopes,
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(days=expiry_days)).isoformat()
        }
        
        self.redis.hmset(f'api_key:{key_hash}', key_data)
        return api_key
    
    def validate_api_key(self, api_key: str) -> Optional[Dict]:
        """Validate an API key and return its metadata."""
        if not api_key:
            return None
            
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        key_data = self.redis.hgetall(f'api_key:{key_hash}')
        
        if not key_data:
            return None
            
        # Check expiration
        expires_at = datetime.fromisoformat(key_data['expires_at'])
        if expires_at < datetime.utcnow():
            self.revoke_api_key(api_key)
            return None
            
        return key_data
    
    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke an API key."""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        return bool(self.redis.delete(f'api_key:{key_hash}'))
    
    def generate_jwt(self, user_id: str, scopes: List[str], expiry_minutes: int = 60) -> str:
        """Generate a JWT token for a user."""
        payload = {
            'user_id': user_id,
            'scopes': scopes,
            'exp': datetime.utcnow() + timedelta(minutes=expiry_minutes),
            'iat': datetime.utcnow(),
            'jti': secrets.token_hex(16)
        }
        
        return jwt.encode(
            payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )
    
    def validate_jwt(self, token: str) -> Optional[Dict]:
        """Validate a JWT token and return its payload."""
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            
            # Check if token is blacklisted
            if payload['jti'] in self._token_blacklist:
                return None
                
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def blacklist_jwt(self, token: str) -> bool:
        """Add a JWT token to the blacklist."""
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            self._token_blacklist.add(payload['jti'])
            return True
        except:
            return False

def require_auth(required_scopes: List[str] = None):
    """Decorator to require authentication and optional scopes."""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return jsonify({
                    'error': {
                        'code': 'UNAUTHORIZED',
                        'message': 'No authorization header'
                    }
                }), 401
            
            try:
                auth_type, token = auth_header.split()
                if auth_type.lower() not in ('bearer', 'jwt'):
                    raise ValueError('Invalid authorization type')
            except ValueError:
                return jsonify({
                    'error': {
                        'code': 'UNAUTHORIZED',
                        'message': 'Invalid authorization header format'
                    }
                }), 401
            
            # Get auth manager instance
            auth_manager = current_app.auth_manager
            
            # Validate token based on type
            if auth_type.lower() == 'bearer':
                token_data = auth_manager.validate_api_key(token)
            else:  # JWT
                token_data = auth_manager.validate_jwt(token)
            
            if not token_data:
                return jsonify({
                    'error': {
                        'code': 'UNAUTHORIZED',
                        'message': 'Invalid or expired token'
                    }
                }), 401
            
            # Check scopes if required
            if required_scopes:
                token_scopes = set(token_data.get('scopes', []))
                if not all(scope in token_scopes for scope in required_scopes):
                    return jsonify({
                        'error': {
                            'code': 'FORBIDDEN',
                            'message': 'Insufficient permissions'
                        }
                    }), 403
            
            # Add token data to request context
            request.token_data = token_data
            return f(*args, **kwargs)
        return wrapped
    return decorator

class RateLimiter:
    """Rate limiting implementation using Redis."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """Initialize rate limiter with Redis connection."""
        self.redis = redis.from_url(redis_url)
    
    def is_allowed(self, key: str, limit: int, window: int = 60) -> bool:
        """Check if request is allowed under rate limit."""
        current = int(time.time())
        window_key = f'{key}:{current // window}'
        
        with self.redis.pipeline() as pipe:
            pipe.incr(window_key)
            pipe.expire(window_key, window)
            current_count = pipe.execute()[0]
        
        return current_count <= limit
    
    def get_limit_headers(self, key: str, limit: int, window: int = 60) -> Dict[str, str]:
        """Get rate limit headers for response."""
        current = int(time.time())
        window_key = f'{key}:{current // window}'
        
        remaining = limit - int(self.redis.get(window_key) or 0)
        reset = (current // window + 1) * window
        
        return {
            'X-RateLimit-Limit': str(limit),
            'X-RateLimit-Remaining': str(max(0, remaining)),
            'X-RateLimit-Reset': str(reset)
        }

def rate_limit(limit: int, window: int = 60):
    """Decorator to apply rate limiting."""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Get rate limiter instance
            rate_limiter = current_app.rate_limiter
            
            # Get identifier (API key or IP)
            identifier = (request.token_data.get('user_id') if hasattr(request, 'token_data')
                        else request.remote_addr)
            
            if not rate_limiter.is_allowed(identifier, limit, window):
                return jsonify({
                    'error': {
                        'code': 'RATE_LIMIT_EXCEEDED',
                        'message': 'Rate limit exceeded'
                    }
                }), 429
            
            response = f(*args, **kwargs)
            
            # Add rate limit headers to response
            if isinstance(response, tuple):
                response, status_code = response
            else:
                status_code = 200
            
            headers = rate_limiter.get_limit_headers(identifier, limit, window)
            
            if isinstance(response, dict):
                return jsonify(response), status_code, headers
            return response, status_code, headers
            
        return wrapped
    return decorator
