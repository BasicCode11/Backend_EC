# app/core/middleware.py
import time
from collections import defaultdict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.responses import JSONResponse
from .config import settings
from app.core.logging import get_logger

logger = get_logger("middleware")



# Logging Middleware

class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all incoming requests and outgoing responses with duration."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        logger.info(f"➡️ {request.method} {request.url.path} from {request.client.host}")

        response: Response = await call_next(request)

        duration = (time.time() - start_time) * 1000
        logger.info(
            f"⬅️ {request.method} {request.url.path} "
            f"Status: {response.status_code} "
            f"Duration: {duration:.2f}ms"
        )
        return response



# Rate Limiting Middleware

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiting middleware.
    - Global limit per IP
    - Optional stricter limits per route (e.g., login)
    """

    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.client_requests = defaultdict(list)  # {client_ip:path: [timestamps]}

        # Stricter per-route limits
        self.route_limits = {
            "/token": (5, 60),      # 5 requests per minute on login
            "/auth/login": (5, 60), # alternative login path
        }

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        path = request.url.path
        current_time = time.time()

        max_req, window = self.route_limits.get(path, (self.max_requests, self.window_seconds))

        key = f"{client_ip}:{path}"
        timestamps = self.client_requests[key]

        # Remove old timestamps outside the window
        self.client_requests[key] = [t for t in timestamps if t > current_time - window]

        if len(self.client_requests[key]) >= max_req:
            logger.warning(f"🚫 Rate limit exceeded for {client_ip} on {path}")
            return JSONResponse(
                status_code=429,
                content={
                    "status": "error",
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": f"Too many requests. Limit: {max_req} per {window} seconds.",
                },
            )

        # Add current request timestamp
        self.client_requests[key].append(current_time)

        response: Response = await call_next(request)
        return response


# Security Headers Middleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add standard security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response



# Register Middlewares

def register_middlewares(app, enable_https: bool = False):
    """Register all middlewares for the FastAPI app."""

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,  # Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Logging
    app.add_middleware(LoggingMiddleware)

    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # HTTPS redirect (optional, production)
    if enable_https:
        app.add_middleware(HTTPSRedirectMiddleware)

    # Rate limiting
    app.add_middleware(RateLimitMiddleware)

    logger.info("✅ Middlewares registered")
