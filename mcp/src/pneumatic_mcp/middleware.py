"""HTTP policy around the SDK's authentication and transport middleware."""

from starlette.datastructures import MutableHeaders
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from pneumatic_mcp.errors import AuthUnavailable


class McpEnabledMiddleware:
    def __init__(self, app: ASGIApp, enabled: bool):
        self.app = app
        self.enabled = enabled

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http" and not self.enabled:
            return await JSONResponse({"error": "disabled"}, status_code=503)(
                scope, receive, send
            )
        await self.app(scope, receive, send)


class OAuthResponseMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def send_response(message: Message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                if challenge := scope.get("mcp_auth_challenge"):
                    message["status"] = scope["mcp_auth_status"]
                    headers["WWW-Authenticate"] = challenge
                elif message["status"] == 401:
                    challenge = headers.get("WWW-Authenticate", "")
                    if challenge and "scope=" not in challenge:
                        headers["WWW-Authenticate"] = (
                            challenge + ', scope="pneumatic:read"'
                        )
                if status := scope.get("mcp_status"):
                    message["status"] = status
                    headers["Retry-After"] = "60" if status == 429 else "1"
            await send(message)

        try:
            await self.app(scope, receive, send_response)
        except AuthUnavailable:
            await JSONResponse(
                {"error": "authorization_unavailable"},
                status_code=503,
                headers={"Retry-After": "1"},
            )(scope, receive, send)


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def send_response(message: Message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["Cache-Control"] = "no-store"
                headers["Referrer-Policy"] = "no-referrer"
            await send(message)

        await self.app(scope, receive, send_response)
