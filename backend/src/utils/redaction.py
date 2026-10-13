import json
import re
from typing import Any, Optional

from django.conf import settings


REDACTED = '[REDACTED]'
SENSITIVE_KEYS = frozenset(
    {
        'authorization',
        'cookie',
        'set_cookie',
        'x_mcp_service_secret',
        'x_mcp_file_service_secret',
        'access_token',
        'refresh_token',
        'source_token',
        'token',
        'credential',
        'client_secret',
        'code',
        'code_verifier',
        'registration_access_token',
        'source_url',
        'query_string',
        'body',
        'args',
        'kwargs',
        'vars',
        'data',
    },
)
MCP_MARKERS = (
    '/oauth/mcp/',
    '/internal/mcp/',
    '/integrations/mcp/',
    '/mcp/',
    'src.mcp.',
    'src.authentication.services.mcp_auth',
    'src.authentication.services.mcp_oauth',
    'src.authentication.services.delegation',
    'src.authentication.services.consent',
    'src.authentication.views.oauth',
    'mcp-d_',
    'mcp-u_',
    'x-mcp-service-secret',
    'x-mcp-file-service-secret',
    'mcp_service_secret',
    'mcp_file_service_secret',
    'src\\\\mcp\\\\',
)
TOKEN = re.compile(r'mcp-[du]_[A-Za-z0-9_-]+')
TICKET = re.compile(r'(/(?:files/)?mcp/download/)[^/?\s\"\']+')
URL_QUERY = re.compile(r'(https?://[^\s?\"\']+)\?[^\s\"\']+')
FORM_SECRET = re.compile(
    r'(?i)((?:access_token|refresh_token|client_secret|credential|'
    r'code_verifier|code|token)=)[^&\s\"\']+',
)


def redact_event(event: dict, hint: Optional[dict] = None) -> dict:
    """Sentry hook: strip MCP credentials from an event.

    Delegated tokens and download tickets are removed from every event.
    Events produced by MCP code additionally lose sensitive keys, URL
    queries, form secrets and the configured service secrets.
    """
    is_mcp = (
        event.get('tags', {}).get('mcp') == 'true'
        or _contains_mcp_marker(event=event)
    )
    secrets = [
        secret
        for secret in (
            settings.MCP_SERVICE_SECRET,
            settings.MCP_FILE_SERVICE_SECRET,
        )
        if secret
    ]
    return _scrub(value=event, is_mcp=is_mcp, secrets=secrets)


def _contains_mcp_marker(event: dict) -> bool:
    serialized = json.dumps(event, default=str).lower()
    return any(marker in serialized for marker in MCP_MARKERS)


def _scrub(value: Any, is_mcp: bool, secrets: list[str]) -> Any:
    if isinstance(value, dict):
        return {
            key: (
                REDACTED
                if is_mcp and _is_sensitive_key(key=key)
                else _scrub(value=item, is_mcp=is_mcp, secrets=secrets)
            )
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [
            _scrub(value=item, is_mcp=is_mcp, secrets=secrets)
            for item in value
        ]
    if isinstance(value, str):
        return _scrub_string(value=value, is_mcp=is_mcp, secrets=secrets)
    return value


def _is_sensitive_key(key: Any) -> bool:
    return str(key).lower().replace('-', '_') in SENSITIVE_KEYS


def _scrub_string(value: str, is_mcp: bool, secrets: list[str]) -> str:
    value = TOKEN.sub(REDACTED, value)
    value = TICKET.sub(rf'\1{REDACTED}', value)
    if not is_mcp:
        return value
    value = URL_QUERY.sub(rf'\1?{REDACTED}', value)
    value = FORM_SECRET.sub(rf'\1{REDACTED}', value)
    for secret in secrets:
        value = value.replace(secret, REDACTED)
    return value
