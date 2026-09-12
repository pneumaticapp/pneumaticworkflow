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
REQUEST_ID_PATTERN = re.compile(r'^[A-Za-z0-9._~+/=-]{1,64}\Z')
FALLBACK_IP = '0.0.0.0'  # noqa: S104
REAL_IP_HEADER = 'X-Real-IP'
USER_AGENT_HEADER = 'User-Agent'


def get_client_ip(request: Request) -> str:
    """Extract client IP securely.

    Relies on X-Real-IP set by Nginx ($remote_addr).
    Ignores X-Forwarded-For which can be spoofed by clients.

    Behind somebody else's balancer X-Real-IP is client controlled,
    so the value is kept only when it really is an address: anything
    else would ride in every record of the request, and in the key of
    the rate limit bucket, at whatever length the client chose.

    This is stricter than the backend on purpose: backend/src/utils/
    http.py falls back to the first hop of X-Forwarded-For, which is
    client controlled in the same situation. Behind our own nginx
    both read X-Real-IP and agree; behind a foreign one this service
    prefers the socket address to a header anybody can write. No test
    compares the two: the difference is deliberate, so a change to the
    order of trust on either side has to be made on both by hand.
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
    """Return the id RequestIdMiddleware stored on the request.

    One source and no fallback: RequestIdMiddleware is the outermost
    middleware of the application, so the id is always there, and it
    is the id every response the application builds carries in its
    X-Request-ID header (a 500 of the server error handler outside
    that stack carries none). Minting another one here would put an
    id into a record that the caller never saw.
    """
    request_id: str = request.state.request_id
    return request_id


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
