"""FastAPI application entry point."""

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.infra.http_client import close_shared_client, get_shared_client
from src.infra.repositories import StorageServiceHolder
from src.presentation.api import files_router
from src.shared_kernel.auth import close_redis_client
from src.shared_kernel.config import get_settings
from src.shared_kernel.exceptions import register_exception_handlers
from src.shared_kernel.middleware import AuthenticationMiddleware
from src.shared_kernel.middleware.rate_limit import RateLimitMiddleware
from src.shared_kernel.middleware.security_headers import (
    SecurityHeadersMiddleware,
)

# Get settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan event handlers."""
    # Initialize shared HTTP client
    get_shared_client()
    yield
    # Close services on shutdown
    await StorageServiceHolder.close()
    await close_redis_client()
    await close_shared_client()

# Create application
app = FastAPI(
    title='Pneumatic Files Service',
    description='File proxy microservice with Google Cloud Storage',
    version='0.1.0',
    openapi_url='/openapi.json' if settings.CONFIG != 'Production' else None,
    docs_url='/docs' if settings.CONFIG != 'Production' else None,
    redoc_url='/redoc' if settings.CONFIG != 'Production' else None,
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PUT', 'DELETE'],
    allow_headers=[
        'Authorization',
        'Content-Type',
        'X-Guest-Authorization',
        'X-Public-Authorization',
    ],
)

# Authentication middleware
app.add_middleware(
    AuthenticationMiddleware,  # type: ignore[arg-type]
    require_auth=True,
)

# Rate limiting middleware (disabled in debug/test mode)
app.add_middleware(
    RateLimitMiddleware,  # type: ignore[arg-type]
    enabled=not settings.DEBUG,
)

# Security headers middleware
app.add_middleware(
    SecurityHeadersMiddleware,  # type: ignore[arg-type]
    include_hsts=settings.CONFIG == 'Production',
)

# Register exception handlers
register_exception_handlers(app)

# Include routers
app.include_router(files_router)

if __name__ == '__main__':
    uvicorn.run(
        'src.main:app',
        host='0.0.0.0',
        port=settings.PORT,
        reload=settings.CONFIG != 'Production',
        workers=1 if settings.CONFIG != 'Production' else settings.WORKERS,
    )
