from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Optional

from src.authentication.enums import AuthTokenType
from src.logs.events.enums import ActorType, actor_type_from_auth
from src.utils.http import get_client_ip

USER_AGENT_MAX = 500
CONTEXT_VAR_NAME = 'pneumatic_event_context'


@dataclass
class RequestContext:

    """ Data of the current HTTP request for emit() calls made deep
        in services, where the request object is not passed around. """

    request_id: Optional[str] = None
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    actor_type: ActorType.LITERALS = ActorType.SYSTEM
    actor_id: Optional[int] = None
    actor_email: Optional[str] = None
    account_id: Optional[int] = None


_context: ContextVar = ContextVar(CONTEXT_VAR_NAME, default=None)


def set_context(context: RequestContext) -> Token:

    """ Return the token needed to restore the previous value. """

    return _context.set(context)


def reset_context(token: Token) -> None:
    _context.reset(token)


def get_context() -> Optional[RequestContext]:
    return _context.get()


def get_user_agent_header(request) -> Optional[str]:

    """ Raw User-Agent header, trimmed to a sane length. """

    user_agent = request.META.get('HTTP_USER_AGENT')
    if not user_agent:
        return None
    return user_agent[:USER_AGENT_MAX]


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
        context.actor_type = actor_type_from_auth(auth_type)
        context.actor_id = user.id
        context.actor_email = getattr(user, 'email', None)
        context.account_id = getattr(user, 'account_id', None)
    return context
