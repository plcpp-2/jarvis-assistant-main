from datetime import datetime, timedelta
from typing import Dict, Optional
import jwt
from dataclasses import dataclass
import bcrypt
import logging
from aiohttp import web
from functools import wraps

logger = logging.getLogger(__name__)


@dataclass
class User:
    username: str
    role: str
    password_hash: str


class AuthManager:
    def __init__(self, secret_key: str, token_expiry: int = 24):
        self.secret_key = secret_key
        self.token_expiry = token_expiry  # hours
        self.users: Dict[str, User] = {}
        self.rate_limits: Dict[str, list] = {}
        self.max_requests = 100  # requests per minute

    def add_user(self, username: str, password: str, role: str = "user"):
        """Add a new user"""
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        self.users[username] = User(username=username, role=role, password_hash=password_hash)

    def verify_password(self, username: str, password: str) -> bool:
        """Verify user password"""
        user = self.users.get(username)
        if not user:
            return False
        return bcrypt.checkpw(password.encode(), user.password_hash)

    def create_token(self, username: str) -> str:
        """Create JWT token"""
        user = self.users.get(username)
        if not user:
            raise ValueError("User not found")

        payload = {
            "username": username,
            "role": user.role,
            "exp": datetime.utcnow() + timedelta(hours=self.token_expiry),
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token"""
        try:
            return jwt.decode(token, self.secret_key, algorithms=["HS256"])
        except jwt.InvalidTokenError:
            return None

    def check_rate_limit(self, username: str) -> bool:
        """Check if user has exceeded rate limit"""
        now = datetime.now()
        user_requests = self.rate_limits.get(username, [])

        # Remove old requests
        user_requests = [time for time in user_requests if time > now - timedelta(minutes=1)]

        # Update requests
        self.rate_limits[username] = user_requests

        # Check limit
        if len(user_requests) >= self.max_requests:
            return False

        # Add new request
        user_requests.append(now)
        return True


def require_auth(f):
    """Decorator to require authentication"""

    @wraps(f)
    async def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise web.HTTPUnauthorized(reason="Missing or invalid authorization header")

        token = auth_header.split(" ")[1]
        auth_manager = request.app["auth_manager"]

        payload = auth_manager.verify_token(token)
        if not payload:
            raise web.HTTPUnauthorized(reason="Invalid token")

        username = payload["username"]
        if not auth_manager.check_rate_limit(username):
            raise web.HTTPTooManyRequests(reason="Rate limit exceeded")

        request["user"] = payload
        return await f(request, *args, **kwargs)

    return wrapper


def require_role(role: str):
    """Decorator to require specific role"""

    def decorator(f):
        @wraps(f)
        async def wrapper(request, *args, **kwargs):
            user = request.get("user")
            if not user or user["role"] != role:
                raise web.HTTPForbidden(reason="Insufficient permissions")
            return await f(request, *args, **kwargs)

        return wrapper

    return decorator
