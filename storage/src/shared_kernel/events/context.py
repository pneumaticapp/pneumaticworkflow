"""HTTP context of a record, taken from the request it came with."""

from fastapi import Request

from src.shared_kernel.events.schema import RequestContext
from src.shared_kernel.http_context import (
    get_client_ip,
    get_request_id,
    get_user_agent,
)


def get_request_context(request: Request) -> RequestContext:
    """Everything a record takes from the request itself."""
    return RequestContext(
        ip=get_client_ip(request),
        user_agent=get_user_agent(request),
        request_id=get_request_id(request),
    )
