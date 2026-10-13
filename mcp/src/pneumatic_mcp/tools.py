"""Authenticated tool execution and protocol responses."""

import asyncio
import json
import logging
import re
from urllib.parse import urlsplit
from uuid import UUID

import mcp_types as types
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import AccessToken
from mcp.server.context import CallNext, ServerRequestContext
from mcp.shared.exceptions import MCPError
from pydantic import JsonValue, ValidationError

from pneumatic_mcp.auth import auth_challenge
from pneumatic_mcp.client import CoreClient
from pneumatic_mcp.errors import CoreError, public_error
from pneumatic_mcp.files import file_id_segment
from pneumatic_mcp.limiter import RateLimiter
from pneumatic_mcp.normalization import normalize
from pneumatic_mcp.settings import (
    FILES_READ_SCOPE,
    FILES_WRITE_SCOPE,
    READ_SCOPE,
    Settings,
)
from pneumatic_mcp.tool_catalog import TOOL_SPECS, TOOLS, ToolSpec

logger = logging.getLogger(__name__)


def result(
    value: dict, *, error: bool = False, challenge: str | None = None
) -> types.CallToolResult:
    return types.CallToolResult(
        content=[
            types.TextContent(
                type="text", text=json.dumps(value, ensure_ascii=False)
            )
        ],
        structuredContent=value,
        isError=error,
        **(
            {"_meta": {"mcp/www_authenticate": [challenge]}}
            if challenge
            else {}
        ),
    )


def has_upload_reference(value: JsonValue) -> bool:
    if isinstance(value, dict):
        return "upload_id" in value or any(
            has_upload_reference(value=item) for item in value.values()
        )
    return isinstance(value, list) and any(
        has_upload_reference(value=item) for item in value
    )


def has_potential_file_clear(value: JsonValue) -> bool:
    if isinstance(value, dict):
        return any(
            item is None
            or item == []
            or item == ""
            or has_potential_file_clear(value=item)
            for item in value.values()
        )
    return isinstance(value, list) and any(
        has_potential_file_clear(value=item) for item in value
    )


def has_public_file_reference(value: JsonValue, settings: Settings) -> bool:
    if isinstance(value, dict):
        return any(
            has_public_file_reference(value=item, settings=settings)
            for item in value.values()
        )
    if isinstance(value, list):
        return any(
            has_public_file_reference(value=item, settings=settings)
            for item in value
        )
    if not isinstance(value, str):
        return False
    # Core owns the configured public file prefix and attachment permissions.
    # Detect plain and Markdown URLs at the public frontend /files/ boundary;
    # this never fetches a URL or decides that a file is authorized.
    public = urlsplit(settings.issuer_url.rstrip("/") + "/files/")
    for match in re.finditer(r"https?://[^\s<>()\"']+", value):
        try:
            url = urlsplit(match.group())
            same_origin = (
                url.scheme == public.scheme
                and url.hostname == public.hostname
                and (url.port or (443 if url.scheme == "https" else 80))
                == (public.port or (443 if public.scheme == "https" else 80))
                and url.username is None
                and url.password is None
            )
        except ValueError:
            continue
        if (
            same_origin
            and url.path.startswith(public.path)
            and re.fullmatch(
                r"[A-Za-z0-9_.%-]{8,512}", url.path[len(public.path) :]
            )
        ):
            return True
    return False


class ToolHandlers:
    def __init__(self, core: CoreClient, limiter: RateLimiter):
        self.core = core
        self.limiter = limiter

    async def oauth_metadata(
        self, ctx: ServerRequestContext, call_next: CallNext
    ):
        wire = await call_next(ctx)
        if ctx.method == "tools/list" and isinstance(wire, dict):
            # SDK 2.3's versioned surface removes extension fields. Its public
            # middleware receives the serialized result, so restore this
            # declared
            # OAuth extension here without altering SDK models or protocol
            # handling.
            for tool in wire.get("tools", []):
                spec = TOOLS[tool["name"]]
                tool["securitySchemes"] = [
                    {"type": "oauth2", "scopes": list(spec.scopes)}
                ]
        return wire

    async def _charge(self):
        token = get_access_token()
        if not token:
            raise CoreError(code="unauthorized")
        claims = token.claims or {}
        await self.limiter.acquire(
            connection_id=claims["connection_id"],
            account_id=claims["account_id"],
        )

    async def list_tools(
        self,
        ctx: ServerRequestContext,
        params: types.PaginatedRequestParams | None,
    ):
        try:
            await self._charge()
        except CoreError as exc:
            if ctx.request is not None:
                ctx.request.scope["mcp_status"] = (
                    429 if exc.code == "rate_limited" else 503
                )
            raise MCPError(
                code=-32029, message="Tool discovery temporarily unavailable"
            ) from None
        # Authenticated callers must discover write/file tools before they can
        # request scope upgrades. This catalogue contains no account data.
        return types.ListToolsResult(
            tools=[spec.schema() for spec in TOOL_SPECS]
        )

    async def call_tool(
        self, ctx: ServerRequestContext, params: types.CallToolRequestParams
    ) -> types.CallToolResult:
        spec = TOOLS.get(params.name)
        write = spec.write if spec else True
        required_scopes = spec.scopes if spec else ()
        try:
            if not spec:
                raise CoreError(code="unknown_tool")
            token = get_access_token()
            if not token:
                raise CoreError(code="unauthorized")
            self._require_scopes(token=token, scopes=spec.scopes)
            input_args = self._arguments(spec=spec, arguments=params.arguments)
            required_scopes = self._required_scopes(
                spec=spec, token=token, args=input_args
            )
            self._require_scopes(token=token, scopes=required_scopes)
            delegation_scopes = self._delegation_scopes(
                spec=spec, token=token, required=required_scopes
            )
            await self._charge()
            async with asyncio.timeout(self.core.settings.call_timeout):
                data = await self._execute(
                    spec=spec,
                    token=token,
                    args=input_args,
                    scopes=delegation_scopes,
                )
            return result(
                value=self._normalize(
                    spec=spec, data=data, input_args=input_args
                )
            )
        except TimeoutError:
            return result(
                value=public_error(
                    error=CoreError(code="timeout"), write=write
                ),
                error=True,
            )
        except CoreError as exc:
            return self._error_result(
                ctx=ctx,
                error=exc,
                name=spec.name if spec else "unknown",
                write=write,
                required_scopes=required_scopes,
            )
        except Exception:
            logger.error(
                "tool_result tool=%s code=internal_error",
                spec.name if spec else "unknown",
            )
            return result(
                value=public_error(
                    error=CoreError(code="internal_error"), write=write
                ),
                error=True,
            )

    @staticmethod
    def _require_scopes(token: AccessToken, scopes: tuple[str, ...]) -> None:
        if not set(scopes) <= set(token.scopes):
            raise CoreError(code="insufficient_scope", status=403)

    @staticmethod
    def _arguments(spec: ToolSpec, arguments: dict | None) -> dict:
        try:
            return spec.model.model_validate(arguments or {}).model_dump(
                exclude_none=True
            )
        except ValidationError:
            raise CoreError(code="invalid_arguments") from None

    def _required_scopes(
        self, spec: ToolSpec, token: AccessToken, args: dict
    ) -> tuple[str, ...]:
        required = spec.scopes
        file_values = (
            args.get(spec.field_values) if spec.field_values else None
        )
        if has_upload_reference(value=file_values) or (
            spec.name == "complete_task"
            and FILES_WRITE_SCOPE in token.scopes
            and has_potential_file_clear(value=file_values)
        ):
            required = (*required, FILES_WRITE_SCOPE)
        if spec.file_links and has_public_file_reference(
            value=args, settings=self.core.settings
        ):
            required = (*required, FILES_READ_SCOPE, FILES_WRITE_SCOPE)
        return tuple(dict.fromkeys(required))

    @staticmethod
    def _delegation_scopes(
        spec: ToolSpec, token: AccessToken, required: tuple[str, ...]
    ) -> tuple[str, ...]:
        # Core decides actual field semantics. Preserve already consented file
        # permissions on this path-bound write without demanding a new consent
        # for ordinary text values.
        if not spec.file_links:
            return required
        return tuple(
            dict.fromkeys(
                (
                    *required,
                    *(
                        scope
                        for scope in (FILES_READ_SCOPE, FILES_WRITE_SCOPE)
                        if scope in token.scopes
                    ),
                )
            )
        )

    async def _execute(
        self,
        spec: ToolSpec,
        token: AccessToken,
        args: dict,
        scopes: tuple[str, ...],
    ) -> dict | list:
        path = spec.path.format(**args)
        payload = {
            key: value
            for key, value in args.items()
            if "{" + key + "}" not in spec.path
        }
        data = await self.core.call(
            token=token,
            tool=spec.name,
            scopes=scopes,
            method=spec.method,
            path=path,
            params=payload if not spec.write else None,
            body=payload if spec.write else None,
        )
        if spec.name == "get_attachment":
            return await self._attachment(token=token, data=data)
        return data

    async def _attachment(self, token: AccessToken, data: dict | list) -> dict:
        if not isinstance(data, dict):
            raise CoreError(code="invalid_response")
        file_id = data.get("file_id")
        try:
            segment = file_id_segment(value=file_id)
        except ValueError:
            raise CoreError(code="invalid_response") from None
        metadata = await self.core.call(
            token=token,
            tool="get_file_metadata",
            scopes=(FILES_READ_SCOPE,),
            method="GET",
            path=f"/mcp/files/{segment}",
            audience="pneumatic-files",
        )
        ticket = await self.core.call(
            token=token,
            tool="create_download_ticket",
            scopes=(FILES_READ_SCOPE,),
            method="POST",
            path=f"/mcp/files/{segment}/download-ticket",
            audience="pneumatic-files",
        )
        if (
            not isinstance(metadata, dict)
            or metadata.get("file_id") != file_id
            or not isinstance(ticket, dict)
            or not isinstance(ticket.get("download_url"), str)
        ):
            raise CoreError(code="invalid_response")
        return {
            "attachment": data,
            "file": metadata,
            "download": ticket,
        }

    def _normalize(
        self, spec: ToolSpec, data: dict | list, input_args: dict
    ) -> dict:
        if (
            spec.name == "create_upload_link"
            and isinstance(data, dict)
            and data.get("id")
        ):
            try:
                upload_id = str(UUID(hex=str(data["id"])))
            except ValueError:
                raise CoreError(code="invalid_response") from None
            expected_url = (
                self.core.settings.issuer_url.rstrip("/")
                + f"/mcp/uploads/{upload_id}"
            )
            if data.get("upload_url") != expected_url:
                raise CoreError(code="invalid_response")
        try:
            normalized = normalize(
                name=spec.name,
                raw=data,
                args=input_args,
                output=spec.output,
            )
        except (
            ValidationError,
            TypeError,
            KeyError,
            ValueError,
            AttributeError,
        ):
            raise CoreError(code="invalid_response") from None
        return normalized

    def _error_result(
        self,
        ctx: ServerRequestContext,
        error: CoreError,
        name: str,
        write: bool,
        required_scopes: tuple[str, ...],
    ) -> types.CallToolResult:
        # No exception repr, bodies, headers, identifiers or URLs in logs.
        logger.info(
            "tool_result tool=%s code=%s",
            name,
            error.code,
        )
        challenge = None
        if error.code == "rate_limited" and ctx.request is not None:
            ctx.request.scope["mcp_status"] = 429
        if (
            error.code == "authorization_unavailable"
            and ctx.request is not None
        ):
            ctx.request.scope["mcp_status"] = 503
        if error.code in {"insufficient_scope", "unauthorized"}:
            if error.required_scopes:
                required_scopes = tuple(
                    dict.fromkeys((*required_scopes, *error.required_scopes))
                )
            challenge = auth_challenge(
                settings=self.core.settings,
                error="invalid_token"
                if error.code == "unauthorized"
                else error.code,
                scopes=required_scopes or (READ_SCOPE,),
            )
            if ctx.request is not None:
                ctx.request.scope["mcp_auth_challenge"] = challenge
                ctx.request.scope["mcp_auth_status"] = (
                    401 if error.code == "unauthorized" else 403
                )
        return result(
            value=public_error(error=error, write=write),
            error=True,
            challenge=challenge,
        )
