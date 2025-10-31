from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler , Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from fastapi.staticfiles import StaticFiles

from .core.config import settings
from .database import Base, engine
from .core.middleware import  register_middlewares 
from .routers.role_router import router as role_router
from .routers.permission_router import router as permission_router
from .routers.user_route import router as user_router
from .routers.auth_router import router as auth_router
from .routers.audit_log_router import router as audit_log_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    print("Database tables created")
    yield
    print("Shutting down...")

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="FastAPI Application",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth_router, prefix="/api", tags=["Auth"])
app.include_router(user_router, prefix="/api", tags=["Users"])
app.include_router(role_router, prefix="/api", tags=["Roles"])
app.include_router(permission_router, prefix="/api", tags=["Permissions"])
app.include_router(audit_log_router, prefix="/api", tags=["Audit Logs"])

@app.get("/", tags=["health"])
def health():
    return {"status": "ok"}