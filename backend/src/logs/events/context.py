from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Optional

from src.authentication.enums import AuthTokenType
from src.logs.events.enums import actor_type_from_auth
from src.logs.events.schema import Actor
from src.utils.http import (
    get_client_ip,
    get_user_agent_header,
)

CONTEXT_VAR_NAME = 'pneumatic_event_context'


@dataclass
class RequestContext:

    """ Data of the current HTTP request for emit() calls made deep
        in services, where the request object is not passed around. """

    request_id: Optional[str] = None
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    actor: Optional[Actor] = None


_context: ContextVar = ContextVar(CONTEXT_VAR_NAME, default=None)


def set_context(context: RequestContext) -> Token:

    """ Return the token needed to restore the previous value. """

    return _context.set(context)


def reset_context(token: Token) -> None:
    _context.reset(token)


def get_context() -> Optional[RequestContext]:
    return _context.get()


def context_from_request(request) -> RequestContext:

    """ Build the context of an incoming request.

        DRF authenticates after the middleware chain, so at this point
        the actor is known only for session authenticated requests
        (admin site). Token authenticated views pass request= to emit()
        and the actor is taken from request.user there. """

    context = RequestContext(
        request_id=getattr(request, 'request_id', None),
        ip=get_client_ip(request),
        user_agent=get_user_agent_header(request),
    )
    user = getattr(request, 'user', None)
    if user is not None and getattr(user, 'is_authenticated', False):
        auth_type = getattr(request, 'token_type', None) or AuthTokenType.USER
        context.actor = Actor(
            type=actor_type_from_auth(auth_type),
            id=user.id,
            email=getattr(user, 'email', None),
        )
    return context


def merge_context(request) -> RequestContext:

    """ What the pipeline knows about the current request.

        The request the caller handles wins over the context the
        middleware published, field by field: a view that passes
        request= is authenticated by then, while the middleware ran
        before DRF and may have seen an anonymous one. Whatever the
        request does not say falls back to the context. """

    context = get_context()
    if request is None:
        return context or RequestContext()
    from_request = context_from_request(request)
    if context is None:
        return from_request
    return RequestContext(
        request_id=from_request.request_id or context.request_id,
        ip=from_request.ip or context.ip,
        user_agent=from_request.user_agent or context.user_agent,
        actor=from_request.actor or context.actor,
    )
