"""What a request says about its client: address, agent, correlation id.

Read by the middleware (request id, rate limit) and by the audit
journal. It lives outside both so that neither depends on the other:
the rate limiter has no business importing the journal.
"""

import ipaddress
import re
from uuid import uuid4

from fastapi import Request

USER_AGENT_MAX = 500
REQUEST_ID_HEADER = 'X-Request-ID'
REQUEST_ID_HEADER_KEY = REQUEST_ID_HEADER.lower()
REQUEST_ID_PATTERN = re.compile(r'^[A-Za-z0-9._~+/=-]{1,64}\Z')
FALLBACK_IP = '0.0.0.0'  # noqa: S104
REAL_IP_HEADER = 'x-real-ip'
USER_AGENT_HEADER = 'user-agent'


def get_client_ip(request: Request) -> str:
    """Extract client IP securely.

    Relies on X-Real-IP set by Nginx ($remote_addr).
    Ignores X-Forwarded-For which can be spoofed by clients.

    Behind somebody else's balancer X-Real-IP is client controlled,
    so the value is kept only when it really is an address: anything
    else would ride in every record of the request, and in the key of
    the rate limit bucket, at whatever length the client chose.
    """
    real_ip = _valid_ip(request.headers.get(REAL_IP_HEADER))
    if real_ip:
        return real_ip
    return request.client.host if request.client else FALLBACK_IP


def get_user_agent(request: Request) -> str | None:
    """Raw User-Agent, cut to what a record may carry."""
    user_agent = request.headers.get(USER_AGENT_HEADER)
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


def _valid_ip(value: str | None) -> str | None:
    """Return the value when it is an IP address, None otherwise."""
    if not value:
        return None
    address = value.strip()
    try:
        ipaddress.ip_address(address)
    except ValueError:
        return None
    return address
