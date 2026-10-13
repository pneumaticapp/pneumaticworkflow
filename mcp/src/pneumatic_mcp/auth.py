"""Official SDK TokenVerifier backed by private core introspection, without
a cache."""

import asyncio
import re
import time

from mcp.server.auth.provider import AccessToken
from mcp.server.auth.routes import build_resource_metadata_url
from pydantic import AnyHttpUrl

from pneumatic_mcp.client import CoreClient
from pneumatic_mcp.errors import AuthUnavailable, CoreError
from pneumatic_mcp.settings import SCOPES, Settings


def auth_challenge(
    settings: Settings, *, error: str, scopes: tuple[str, ...]
) -> str:
    # Fixed text only: upstream messages and caller arguments must never enter
    # headers.
    descriptions = {
        "insufficient_scope": (
            "Additional permissions are required for this tool."
        ),
        "invalid_token": "Authentication is required. Reconnect this account.",
    }
    metadata_url = build_resource_metadata_url(AnyHttpUrl(settings.public_url))
    return (
        f'Bearer error="{error}", error_description="{descriptions[error]}", '
        f'scope="{" ".join(scopes)}", resource_metadata="{metadata_url}"'
    )


class CoreTokenVerifier:
    def __init__(self, core: CoreClient):
        self.core = core

    async def verify_token(self, token: str) -> AccessToken | None:
        if len(token) > 4096 or not re.fullmatch(
            r"[A-Za-z0-9._~+/-]{16,4096}=*", token
        ):
            return None
        try:
            async with asyncio.timeout(
                self.core.settings.connect_timeout
                + self.core.settings.read_timeout
            ):
                data = await self.core.introspect(token=token)
        except (CoreError, TimeoutError):
            raise AuthUnavailable from None
        if data.get("active") is False:
            return None
        # A broken/private-auth-failing introspection service is not a bad user
        # token.
        if (
            data.get("active") is not True
            or not isinstance(data.get("exp"), int)
            or isinstance(data.get("exp"), bool)
            or not isinstance(data.get("scope"), str)
            or any(
                data.get(key) is None
                for key in (
                    "user_id",
                    "account_id",
                    "client_id",
                    "connection_id",
                    "aud",
                )
            )
        ):
            raise AuthUnavailable
        expiry = data["exp"]
        scopes = data["scope"].split()
        identity = [
            data[key]
            for key in ("user_id", "account_id", "client_id", "connection_id")
        ]
        if (
            data["aud"]
            not in (
                self.core.settings.public_url,
                [self.core.settings.public_url],
            )
            or expiry <= time.time()
            or not scopes
            or not set(scopes) <= SCOPES
            or any(
                not isinstance(value, str | int)
                or isinstance(value, bool)
                or not str(value)
                for value in identity
            )
            or (
                data.get("sub") is not None
                and str(data["sub"]) != str(data["user_id"])
            )
        ):
            return None
        # Connection + tenant + user identify the principal even with a shared
        # OAuth client.
        subject = f"{identity[1]}:{identity[0]}:{identity[3]}"
        return AccessToken(
            token=token,
            client_id=str(data["client_id"]),
            scopes=scopes,
            expires_at=expiry,
            resource=self.core.settings.public_url,
            subject=subject,
            claims={
                "iss": self.core.settings.issuer_url,
                "user_id": data["user_id"],
                "account_id": data["account_id"],
                "connection_id": data["connection_id"],
            },
        )
