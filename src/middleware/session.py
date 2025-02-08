from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from src.services.cache_service import RedisCache
from src.utils.logger import logger
import time
import uuid

class SessionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.cache = RedisCache()
    
    async def dispatch(self, request: Request, call_next):
        # Generate or get session ID
        session_id = request.cookies.get("session_id") or str(uuid.uuid4())
        
        # Track request in Redis
        await self.cache.set(
            f"session:{session_id}:last_active",
            int(time.time()),
            expiry=3600
        )
        
        # Add session info to request state
        request.state.session_id = session_id
        
        response = await call_next(request)
        
        # Set session cookie if not exists
        if not request.cookies.get("session_id"):
            response.set_cookie(
                "session_id",
                session_id,
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=3600
            )
        
        return response 