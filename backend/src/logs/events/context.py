from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Optional

from django.http import HttpRequest

from src.utils.http import (
    get_client_ip,
    get_user_agent_header,
)


@dataclass
class RequestContext:

    """ Data of the current HTTP request for emit() calls made deep
        in services, where the request object is not passed around. """

    request_id: Optional[str] = None
    ip: Optional[str] = None
    user_agent: Optional[str] = None


_context: ContextVar[Optional[RequestContext]] = ContextVar(
    'pneumatic_event_context',
    default=None,
)


def set_context(context: RequestContext) -> Token:

    """ Return the token needed to restore the previous value. """

    return _context.set(context)


def reset_context(token: Token) -> None:
    _context.reset(token)


def get_context() -> Optional[RequestContext]:
    return _context.get()


def context_from_request(request: HttpRequest) -> RequestContext:

    """ Build the context of an incoming request. Who acts is not
        here: DRF authenticates after the middleware chain, and the
        view names the actor in its call of AuditEventService. """

    return RequestContext(
        request_id=getattr(request, 'request_id', None),
        ip=get_client_ip(request),
        user_agent=get_user_agent_header(request),
    )
