"""FastAPI application entry point."""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.presentation.api import files_router
from src.shared_kernel.config import get_settings
from src.shared_kernel.exceptions import register_exception_handlers
from src.shared_kernel.middleware import AuthenticationMiddleware

# Get settings
settings = get_settings()

# Create application
app = FastAPI(
    title='Pneumatic Files Service',
    description='File proxy microservice with Google Cloud Storage',
    version='0.1.0',
    openapi_url='/openapi.json' if settings.CONFIG != 'Production' else None,
    docs_url='/docs' if settings.CONFIG != 'Production' else None,
    redoc_url='/redoc' if settings.CONFIG != 'Production' else None,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PUT', 'DELETE'],
    allow_headers=['*'],
)

# Authentication middleware
app.add_middleware(
    AuthenticationMiddleware,  # type: ignore[arg-type]
    require_auth=True,
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
