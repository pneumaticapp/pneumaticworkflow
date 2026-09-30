from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Optional


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


def reset_context(token: Token):
    _context.reset(token)


def get_context() -> Optional[RequestContext]:
    return _context.get()
