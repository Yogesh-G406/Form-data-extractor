"""
Langfuse Middleware for FastAPI
Automatically tracks all API requests and responses with Langfuse
"""
import os
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from langfuse import Langfuse


class LangfuseMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically track all API requests with Langfuse"""
    
    def __init__(self, app, langfuse_client: Langfuse = None):
        super().__init__(app)
        self.langfuse = langfuse_client
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Track each request/response"""
        if not self.langfuse:
            return await call_next(request)
        
        # Skip health check and root endpoints to reduce noise
        # TEMPORARILY DISABLED FOR DEBUGGING
        # if request.url.path in ["/", "/health"]:
        #     return await call_next(request)
        
        start_time = time.time()
        trace = None
        
        try:
            # Create trace for this request
            trace = self.langfuse.trace(
                name=f"api_request_{request.method}_{request.url.path}",
                metadata={
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": dict(request.query_params),
                    "client_host": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent", "unknown")
                }
            )
            
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Update trace with response info
            if trace:
                trace.update(
                    output={
                        "status_code": response.status_code,
                        "duration_ms": round(duration * 1000, 2)
                    }
                )
            
            return response
            
        except Exception as e:
            # Track errors
            duration = time.time() - start_time
            
            if trace:
                trace.update(
                    output={
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "duration_ms": round(duration * 1000, 2)
                    }
                )
            
            raise
