"""Streamable HTTP resource server. Core owns OAuth and every file
operation."""

import logging
from contextlib import asynccontextmanager

from mcp.server.auth.routes import build_resource_metadata_url
from mcp.server.auth.settings import AuthSettings
from mcp.server.lowlevel import Server
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import AnyHttpUrl
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from pneumatic_mcp.auth import CoreTokenVerifier
from pneumatic_mcp.client import CoreClient
from pneumatic_mcp.limiter import RateLimiter, RedisRateLimiter
from pneumatic_mcp.middleware import (
    McpEnabledMiddleware,
    OAuthResponseMiddleware,
    SecurityHeadersMiddleware,
)
from pneumatic_mcp.security import configure_redaction
from pneumatic_mcp.settings import SCOPE_ORDER, Settings
from pneumatic_mcp.tool_catalog import TOOLS
from pneumatic_mcp.tools import ToolHandlers


def create_app(
    settings: Settings | None = None,
    *,
    core: CoreClient | None = None,
    limiter: RateLimiter | None = None,
) -> Starlette:
    settings = settings or Settings()
    core = core or CoreClient(settings=settings)
    verifier = CoreTokenVerifier(core=core)
    limiter = limiter or RedisRateLimiter(
        url=settings.redis_url.get_secret_value()
    )
    handlers = ToolHandlers(core=core, limiter=limiter)
    server = Server(
        "Pneumatic",
        version="0.1.0",
        instructions="Use field schemas before writes. Transfer file bytes"
        " through upload links. "
        "After an uncertain write, check current state before retrying.",
        on_list_tools=handlers.list_tools,
        on_call_tool=handlers.call_tool,
        get_tool_input_schema=lambda name: (
            TOOLS[name].model.model_json_schema() if name in TOOLS else None
        ),
    )
    server.middleware.append(handlers.oauth_metadata)

    async def metadata(request: Request):
        return JSONResponse(
            {
                "resource": settings.public_url,
                "authorization_servers": [settings.issuer_url],
                "scopes_supported": list(SCOPE_ORDER),
                "bearer_methods_supported": ["header"],
            },
        )

    http_app = server.streamable_http_app(
        streamable_http_path="/mcp",
        stateless_http=True,
        json_response=True,
        max_request_body_size=settings.max_request_bytes,
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=settings.hosts,
            allowed_origins=settings.origins,
        ),
        auth=AuthSettings(
            issuer_url=settings.issuer_url,
            resource_server_url=settings.public_url,
            validate_token_resource=True,
            required_scopes=[],
        ),
        token_verifier=verifier,
    )
    # Advertise alternative scopes; each tool checks its required permissions.
    http_app.router.routes = [
        # This service has no standalone stream or sessions to delete.
        Route(path="/mcp", endpoint=route.endpoint, methods=["POST"])
        if getattr(route, "path", "") == "/mcp"
        else route
        for route in http_app.router.routes
        if not getattr(route, "path", "").startswith(
            "/.well-known/oauth-protected-resource"
        )
    ]
    http_app.router.routes.extend(
        [
            Route(
                path=build_resource_metadata_url(
                    AnyHttpUrl(settings.public_url)
                ).path,
                endpoint=metadata,
            ),
            Route(
                path="/.well-known/oauth-protected-resource", endpoint=metadata
            ),
        ]
    )
    http_app.router.redirect_slashes = False

    @asynccontextmanager
    async def lifespan(app: Starlette):
        try:
            if settings.enabled:
                async with server.session_manager.run():
                    yield
            else:
                yield
        finally:
            await core.close()
            await limiter.close()

    http_app.router.lifespan_context = lifespan
    http_app.state.core = core
    http_app.state.server = server
    http_app.add_middleware(OAuthResponseMiddleware)
    http_app.add_middleware(McpEnabledMiddleware, enabled=settings.enabled)
    http_app.add_middleware(SecurityHeadersMiddleware)
    # Request logging can contain URL query credentials; do not enable SDK
    # body/debug logs.
    for name in ("httpx", "httpcore", "mcp"):
        logging.getLogger(name).setLevel(logging.WARNING)
    configure_redaction(secret=settings.service_secret.get_secret_value())
    return http_app
