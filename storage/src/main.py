"""FastAPI application entry point."""

import contextlib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from src.infra.adapters import StorageServiceHolder
from src.infra.http_client import close_shared_client, get_shared_client
from src.presentation.api import files_router
from src.shared_kernel.auth import close_redis_client
from src.shared_kernel.config import get_settings
from src.shared_kernel.exceptions import register_exception_handlers
from src.shared_kernel.middleware import AuthenticationMiddleware
from src.shared_kernel.middleware.rate_limit import RateLimitMiddleware
from src.shared_kernel.middleware.security_headers import (
    SecurityHeadersMiddleware,
)

settings = get_settings()


# ── Constants ────────────────────────────────────────────────

API_DESCRIPTION = """\
The Pneumatic Files API provides high-performance file storage \
and streaming capabilities (powered by SeaweedFS / GCS).

### Authentication
Every request requires a `Bearer` token. You can find your \
personal API key inside the app:
1. Go to **Integrations** in the left menu.
2. Copy your key from the **Your API Key** section.

Pass the key in the `Authorization` header:
```http
Authorization: Bearer <your_api_key>
```

Or click the **Authorize** button above and paste your key \
to test endpoints directly.

### Key Capabilities
- **Direct Uploads:** Upload attachments for workflows, tasks, \
and system templates.
- **Resumable & Chunked Uploads:** Stream large attachments efficiently.
- **Secure File Serving:** Range requests, content disposition, \
and instant streaming.
- **Permission Validation:** Automatic permission verification \
against Pneumatic Core Backend.\
"""


# ── Lifespan ─────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan event handlers."""
    get_shared_client()
    yield
    with contextlib.suppress(Exception):
        await StorageServiceHolder.close()
    with contextlib.suppress(Exception):
        await close_redis_client()
    with contextlib.suppress(Exception):
        await close_shared_client()


# ── OpenAPI helpers ──────────────────────────────────────────


def _build_public_docs_paths(application: FastAPI) -> tuple[str, ...]:
    """Path prefixes that bypass authentication (docs UI + schema)."""
    docs_paths = tuple(
        p
        for p in (
            application.docs_url,
            application.redoc_url,
            application.openapi_url,
        )
        if p
    )
    if settings.root_path:
        docs_paths += tuple(f'{settings.root_path}{p}' for p in docs_paths)
    return docs_paths


def _custom_openapi_schema(application: FastAPI) -> dict[str, Any]:
    """Generate OpenAPI schema with security schemes and /files prefix."""
    if application.openapi_schema:
        return application.openapi_schema

    schema = get_openapi(
        title=application.title,
        version=application.version,
        description=application.description,
        routes=application.routes,
        servers=application.servers,
        tags=application.openapi_tags,
    )

    # Nginx strips /files/ on proxy; restore the public prefix so
    # Swagger UI "Try it out" sends requests to the correct path.
    schema['paths'] = {
        path if path.startswith('/files') else f'/files{path}': item
        for path, item in schema.get('paths', {}).items()
    }

    schema.setdefault('components', {})['securitySchemes'] = {
        'tokenAuth': {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'Token',
            'description': (
                'User API key or token (Authorization: Bearer <token>)'
            ),
        },
    }
    schema['security'] = [{'tokenAuth': []}]

    application.openapi_schema = schema
    return schema


# ── Application ──────────────────────────────────────────────

app = FastAPI(
    title='Pneumatic Files API',
    description=API_DESCRIPTION,
    version='1.0.0',
    servers=[
        {
            'url': '/',
            'description': 'Pneumatic Files API Server',
        },
    ],
    openapi_tags=[
        {
            'name': 'files',
            'description': ('Upload, download, and manage file attachments'),
        },
    ],
    root_path=settings.root_path,
    openapi_url='/openapi.json',
    docs_url='/docs',
    redoc_url='/redoc',
    lifespan=lifespan,
)

app.openapi = lambda: _custom_openapi_schema(app)  # type: ignore[method-assign]


# ── Middleware stack ─────────────────────────────────────────
# Order matters: first added = outermost wrapper.

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

app.add_middleware(
    AuthenticationMiddleware,  # type: ignore[arg-type]
    require_auth=True,
    public_paths=_build_public_docs_paths(app),
)

app.add_middleware(
    RateLimitMiddleware,
    enabled=settings.RATE_LIMIT_ENABLED,
)

app.add_middleware(
    SecurityHeadersMiddleware,
    include_hsts=settings.HSTS_ENABLED,
)


# ── Exception handlers & routers ────────────────────────────

register_exception_handlers(app)
app.include_router(files_router)
