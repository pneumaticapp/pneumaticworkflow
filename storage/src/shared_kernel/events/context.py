"""HTTP context of a record: client address, agent, correlation id."""

import re
from uuid import uuid4

from fastapi import Request

from src.shared_kernel.events.schema import RequestContext

USER_AGENT_MAX = 500
REQUEST_ID_HEADER = 'X-Request-ID'
REQUEST_ID_HEADER_KEY = REQUEST_ID_HEADER.lower()
REQUEST_ID_PATTERN = re.compile(r'^[A-Za-z0-9._~+/=-]{1,64}\Z')
FALLBACK_IP = '0.0.0.0'  # noqa: S104


def get_client_ip(request: Request) -> str:
    """Extract client IP securely.

    Relies on X-Real-IP set by Nginx ($remote_addr).
    Ignores X-Forwarded-For which can be spoofed by clients.
    """
    real_ip = request.headers.get('x-real-ip')
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else FALLBACK_IP


def get_user_agent(request: Request) -> str | None:
    """Raw User-Agent, cut to what a record may carry."""
    user_agent = request.headers.get('user-agent')
    if not user_agent:
        return None
    return user_agent[:USER_AGENT_MAX]


def resolve_request_id(value: str | None) -> str:
    """Keep the id of the caller when it is safe to store, else make one."""
    if value and REQUEST_ID_PATTERN.match(value):
        return value
    return uuid4().hex


def get_request_id(request: Request) -> str:
    """Return the id RequestIdMiddleware stored, or a fresh one."""
    request_id = getattr(request.state, 'request_id', None)
    if request_id:
        return request_id
    return resolve_request_id(request.headers.get(REQUEST_ID_HEADER_KEY))


def get_request_context(request: Request) -> RequestContext:
    """Everything a record takes from the request itself."""
    return RequestContext(
        ip=get_client_ip(request),
        user_agent=get_user_agent(request),
        request_id=get_request_id(request),
    )
