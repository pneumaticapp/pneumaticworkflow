"""Bounded core HTTP calls. Redirects, implicit proxy use and retries are
disabled."""

import json
import re
import time
from typing import Any

import httpx
from mcp.server.auth.provider import AccessToken

from pneumatic_mcp.errors import CoreError
from pneumatic_mcp.settings import SCOPES, Settings

DELEGATED_TOKEN = re.compile(r"mcp-d_[A-Za-z0-9_-]{16,512}\Z")
SENSITIVE_KEYS = frozenset(
    {
        "access_token",
        "refresh_token",
        "token",
        "credential",
        "authorization",
        "client_secret",
        "service_secret",
        "mcp_service_secret",
        "password",
    }
)


def redact_result(value: Any, secrets: tuple[str, ...]) -> Any:
    if isinstance(value, dict):
        return {
            key: redact_result(value=item, secrets=secrets)
            for key, item in value.items()
            if key.lower() not in SENSITIVE_KEYS
        }
    if isinstance(value, list):
        return [redact_result(value=item, secrets=secrets) for item in value]
    if isinstance(value, str):
        for secret in secrets:
            if secret:
                value = value.replace(secret, "[REDACTED]")
        return re.sub(r"mcp-d_[A-Za-z0-9_-]+", "[REDACTED]", value)
    return value


class CoreClient:
    def __init__(
        self,
        settings: Settings,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        file_transport: httpx.AsyncBaseTransport | None = None,
    ):
        self.settings = settings
        self.http = self._http_client(transport=transport)
        self.file_http = self._http_client(transport=file_transport)

    def _http_client(
        self, transport: httpx.AsyncBaseTransport | None
    ) -> httpx.AsyncClient:
        settings = self.settings
        return httpx.AsyncClient(
            transport=transport or httpx.AsyncHTTPTransport(retries=0),
            follow_redirects=False,
            trust_env=False,
            timeout=httpx.Timeout(
                settings.read_timeout,
                connect=settings.connect_timeout,
                pool=settings.connect_timeout,
            ),
            limits=httpx.Limits(
                max_connections=settings.max_concurrency,
                max_keepalive_connections=settings.max_concurrency,
            ),
            headers={
                "Accept": "application/json",
                "User-Agent": "Pneumatic-MCP/0.1",
            },
        )

    async def close(self):
        await self.http.aclose()
        await self.file_http.aclose()

    async def _json_body(self, response: httpx.Response) -> Any:
        chunks = bytearray()
        async for chunk in response.aiter_bytes():
            chunks.extend(chunk)
            if len(chunks) > self.settings.max_response_bytes:
                raise CoreError(code="invalid_response")
        if (
            response.headers.get("content-type", "").split(";")[0]
            != "application/json"
        ):
            raise CoreError(code="invalid_response")
        return json.loads(chunks)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        headers: dict,
        body: dict | None = None,
        params: dict | None = None,
        audience: str = "pneumatic-backend",
        private: bool = False,
    ) -> Any:
        try:
            http = (
                self.file_http if audience == "pneumatic-files" else self.http
            )
            endpoint = (
                self.settings.file_endpoint(path=path)
                if audience == "pneumatic-files"
                else self.settings.backend_endpoint(path=path)
            )
            async with http.stream(
                method,
                endpoint,
                headers=headers,
                json=body,
                params=params,
            ) as response:
                if not 200 <= response.status_code < 300:
                    if private and response.status_code == 401:
                        # Only the locked private contract's explicit
                        # source-token
                        # error may prompt user relinking. Service credentials
                        # and
                        # unrecognized/malformed failures are dependency
                        # failures.
                        try:
                            failure = await self._json_body(response=response)
                        except (CoreError, ValueError, UnicodeError):
                            raise CoreError(
                                code="authorization_unavailable", status=503
                            ) from None
                        if (
                            isinstance(failure, dict)
                            and failure.get("code") == "invalid_token"
                        ):
                            raise CoreError(code="unauthorized", status=401)
                        raise CoreError(
                            code="authorization_unavailable", status=503
                        )
                    if response.status_code == 403 and not private:
                        try:
                            failure = await self._json_body(response=response)
                        except (CoreError, ValueError, UnicodeError):
                            raise CoreError(
                                code="forbidden", status=403
                            ) from None
                        if (
                            isinstance(failure, dict)
                            and failure.get("code") == "insufficient_scope"
                        ):
                            required = failure.get("required_scopes")
                            if (
                                not isinstance(required, list)
                                or not 1 <= len(required) <= len(SCOPES)
                                or any(
                                    not isinstance(item, str)
                                    or item not in SCOPES
                                    for item in required
                                )
                            ):
                                raise CoreError(code="invalid_response")
                            raise CoreError(
                                code="insufficient_scope",
                                status=403,
                                required_scopes=tuple(dict.fromkeys(required)),
                            )
                        raise CoreError(code="forbidden", status=403)
                    code = {
                        400: "validation_error",
                        401: "unauthorized",
                        403: "forbidden",
                        404: "not_found",
                        409: "conflict",
                        422: "validation_error",
                        429: "rate_limited",
                    }.get(response.status_code, "unavailable")
                    raise CoreError(code=code, status=response.status_code)
                if response.status_code == 204:
                    return {"ok": True}
                result = await self._json_body(response=response)
                if not isinstance(result, dict | list):
                    raise CoreError(code="invalid_response")
                return result
        except httpx.TimeoutException:
            raise CoreError(code="timeout") from None
        except httpx.HTTPError:
            raise CoreError(code="unavailable") from None
        except (ValueError, UnicodeError):
            raise CoreError(code="invalid_response") from None

    async def private(self, endpoint: str, body: dict) -> dict:
        result = await self._request(
            method="POST",
            path=f"/internal/mcp/{endpoint}",
            body=body,
            headers={
                "X-MCP-Service-Secret": (
                    self.settings.service_secret.get_secret_value()
                )
            },
            private=True,
        )
        if not isinstance(result, dict):
            raise CoreError(code="invalid_response")
        return result

    async def introspect(self, token: str) -> dict:
        return await self.private(
            endpoint="introspect",
            body={"token": token, "resource": self.settings.public_url},
        )

    async def call(
        self,
        *,
        token: AccessToken,
        tool: str,
        scopes: tuple[str, ...],
        method: str,
        path: str,
        body: dict | None = None,
        params: dict | None = None,
        audience: str = "pneumatic-backend",
    ) -> Any:
        grant = await self.private(
            endpoint="delegate",
            body={
                "token": token.token,
                "resource": self.settings.public_url,
                "tool": tool,
                "method": method,
                "path": path,
                "scopes": list(scopes),
            },
        )
        credential = grant.get("credential")
        expiry = grant.get("expires_at")
        lifetime = grant.get("expires_in")
        granted_scopes = grant.get("scopes")
        claims = token.claims or {}
        if (
            not isinstance(credential, str)
            or not DELEGATED_TOKEN.fullmatch(credential)
            or credential == token.token
            or grant.get("token_type") != "Bearer"
            or grant.get("audience") != audience
            or grant.get("operation") != tool
            or not isinstance(expiry, int)
            or isinstance(expiry, bool)
            or not time.time() < expiry <= time.time() + 65
            or not token.expires_at
            or expiry > token.expires_at
            or not isinstance(lifetime, int)
            or isinstance(lifetime, bool)
            or not 0 < lifetime <= 60
            or abs(expiry - time.time() - lifetime) > 2
            or not isinstance(granted_scopes, list)
            or any(not isinstance(item, str) for item in granted_scopes)
            or set(granted_scopes) != set(scopes)
            or any(
                grant.get(key) != claims.get(key)
                for key in ("connection_id", "user_id", "account_id")
            )
        ):
            raise CoreError(code="invalid_response")
        headers = {"Authorization": f"Bearer {credential}"}
        result = await self._request(
            method=method,
            path=path,
            headers=headers,
            body=body,
            params=params,
            audience=audience,
        )
        return redact_result(
            value=result,
            secrets=(
                token.token,
                credential,
                self.settings.service_secret.get_secret_value(),
            ),
        )
