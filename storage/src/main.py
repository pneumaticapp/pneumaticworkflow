"""FastAPI application entry point."""

import contextlib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from copy import deepcopy
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from src.infra.adapters import StorageServiceHolder
from src.infra.http_client import close_shared_client, get_shared_client
from src.presentation.api import files_router
from src.presentation.openapi import (
    BINARY_CONTENT,
    FILES_SECURITY,
    FILES_SECURITY_SCHEMES,
)
from src.shared_kernel.auth import close_redis_client
from src.shared_kernel.config import get_settings
from src.shared_kernel.events import close_event_emitter
from src.shared_kernel.exceptions import register_exception_handlers
from src.shared_kernel.middleware import AuthenticationMiddleware
from src.shared_kernel.middleware.rate_limit import RateLimitMiddleware
from src.shared_kernel.middleware.request_id import RequestIdMiddleware
from src.shared_kernel.middleware.security_headers import (
    SecurityHeadersMiddleware,
)
from src.shared_kernel.sentry import init_sentry

settings = get_settings()
init_sentry()


# ── Constants ────────────────────────────────────────────────

API_DESCRIPTION = """\
Upload files and download their bytes through the configured storage backend.

### Authentication
Both file operations require one valid credential:
- `Authorization: Bearer <API key or session token>`;
- `X-Guest-Authorization: <guest JWT>`;
- `X-Public-Authorization: Token <public or embed template token>`;
- a browser cookie: `file_service_auth` or `token` (user token),
  `guest-token` (guest JWT), or `public-token` (`Token <public/embed token>`).

Headers are checked before cookies, in the order above. Authentication does
not grant access to every file: ownership and Core backend permissions apply.
The OpenAPI document itself is available without a credential.

### Key Capabilities
- **Upload:** Send one multipart `file`; ownership comes from authentication.
  Store the returned `file_id`/URL in the relevant Core workflow/task field.
- **Download:** Return a complete binary stream (200), or a single byte range
  (206), after storage accepts the request. `Range` is forwarded unchanged:
  storage rejection, including `InvalidRange`, becomes API error 503 with
  code `STORAGE_003` and no `Content-Range`. Only when storage accepts the
  stream can the local planner return 416 with `Content-Range` for a range
  unsatisfiable against file metadata. Malformed headers may also be rejected
  by storage; falling back to a full download is not guaranteed.
- **Errors:** Application errors use `code`, `message`, and optional
  `details.reason`. Rate limiting instead returns `detail` and `retry_after`,
  with a `Retry-After` header. Streaming failures after headers are sent may
  terminate the transfer instead of returning a new JSON response.
- **Browser navigation:** GET with `Accept: text/html` may redirect (302)
  to sign-in or the frontend error page. Use `Accept: application/json` when
  integrating to receive JSON errors.

### Deployment limits
The maximum upload size is `MAX_FILE_SIZE` bytes. When rate limiting is
enabled, each client IP has separate sliding-window limits:
`RATE_LIMIT_UPLOAD_REQUESTS` per `RATE_LIMIT_UPLOAD_WINDOW` seconds and
`RATE_LIMIT_DOWNLOAD_REQUESTS` per `RATE_LIMIT_DOWNLOAD_WINDOW` seconds.
These values are configured by the deployment, not a universal API quota.
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
        await close_event_emitter()
    with contextlib.suppress(Exception):
        await close_shared_client()


# ── OpenAPI helpers ──────────────────────────────────────────


def _build_public_docs_paths(application: FastAPI) -> tuple[str, ...]:
    """Path prefixes that bypass authentication (docs UI + schema)."""
    docs_paths = tuple(
        p
        for p in (
            application.docs_url,
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
    # Scalar UI and interactive API clients send requests to the correct path.
    schema['paths'] = {
        path if path.startswith('/files') else f'/files{path}': item
        for path, item in schema.get('paths', {}).items()
    }

    # Describe the existing stream without changing the route response class.
    responses = (
        schema['paths']
        .get('/files/{file_id}', {})
        .get(
            'get',
            {},
        )
        .get('responses', {})
    )
    for status_code in ('200', '206'):
        if status_code in responses:
            responses[status_code]['content'] = deepcopy(BINARY_CONTENT)

    schema.setdefault('components', {})['securitySchemes'] = (
        FILES_SECURITY_SCHEMES
    )
    schema['security'] = FILES_SECURITY

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
            'name': 'Files',
            'description': ('Upload, download, and manage file attachments'),
        },
    ],
    root_path=settings.root_path,
    openapi_url='/openapi.json',
    docs_url=None,
    redoc_url=None,
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

app.add_middleware(RequestIdMiddleware)


# ── Exception handlers & routers ────────────────────────────

register_exception_handlers(app)
app.include_router(files_router)
