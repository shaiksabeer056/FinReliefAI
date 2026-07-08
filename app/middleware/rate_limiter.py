import time
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Tuple

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit_seconds: int = 60, max_requests: int = 100):
        super().__init__(app)
        self.limit_seconds = limit_seconds
        self.max_requests = max_requests
        self.client_records: Dict[str, list] = {}  # IP -> list of timestamps

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        # Clean old timestamps
        if client_ip in self.client_records:
            self.client_records[client_ip] = [
                ts for ts in self.client_records[client_ip]
                if current_time - ts < self.limit_seconds
            ]
        else:
            self.client_records[client_ip] = []

        if len(self.client_records[client_ip]) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )

        self.client_records[client_ip].append(current_time)
        response = await call_next(request)
        return response
