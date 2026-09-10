import logging
from dataclasses import dataclass
from datetime import datetime
from time import monotonic
from typing import Any, Callable, Optional, Tuple

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from src.logs.events.context import (
    RequestContext,
    get_context,
    get_user_agent_header,
)
from src.logs.enums import LogsBackend
from src.logs.events.enums import ActorType
from src.logs.events.registry import resolve_event_type
from src.logs.events.reporting import report_error
from src.logs.events.schema import (
    Actor,
    Event,
    EventObject,
    normalize_payload,
)
from src.logs.events.stream import get_stream
from src.utils.http import get_client_ip

logger = logging.getLogger('pneumatic.events')

NO_ACCOUNT = 0
CIRCUIT_OPEN_SECONDS = 15.0


@dataclass
class StreamCircuit:

    """ Circuit breaker of the write path: one failed write opens it
        for CIRCUIT_OPEN_SECONDS, writes meanwhile are counted and
        dropped, the next write after that closes it again. """

    open_until: float = 0.0
    dropped: int = 0

    def is_open(self, now: float) -> bool:
        return now < self.open_until

    def trip(self, now: float) -> None:
        self.open_until = now + CIRCUIT_OPEN_SECONDS

    def reset(self) -> None:
        self.open_until = 0.0
        self.dropped = 0


_circuit = StreamCircuit()


def emit(
    event_type: str,
    *,
    account_id: Optional[int],
    actor: Optional[Actor] = None,
    event_object: Optional[EventObject] = None,
    payload: Optional[dict] = None,
    workflow_id: Optional[int] = None,
    task_id: Optional[int] = None,
    request=None,
    ts: Optional[datetime] = None,
):

    """ Publish an event to the stream after the current transaction
        commits.

        Writing never raises: it happens in an on_commit callback and
        is wrapped in _write. Building can raise UnknownEventTypeError
        for an undeclared type, but only under the strict
        configurations (see resolve_event_type) so that a typo
        breaks tests instead of production. """

    if settings.LOGS_BACKEND == LogsBackend.NONE:
        return
    event = build_event(
        event_type,
        account_id=account_id,
        actor=actor,
        event_object=event_object,
        payload=payload,
        workflow_id=workflow_id,
        task_id=task_id,
        request=request,
        ts=ts,
    )
    _schedule(event)


def build_event(
    event_type: str,
    *,
    account_id: Optional[int],
    actor: Optional[Actor] = None,
    event_object: Optional[EventObject] = None,
    payload: Optional[dict] = None,
    workflow_id: Optional[int] = None,
    task_id: Optional[int] = None,
    request=None,
    ts: Optional[datetime] = None,
) -> Event:

    """ Fill an event from the registry, the request and the context.

        The caller always wins, then the request it handles, then the
        context published by EventContextMiddleware. """

    declared = resolve_event_type(event_type)
    context = get_context()
    event = Event(
        type=event_type,
        category=declared.category,
        service=settings.LOGS_SERVICE_NAME,
        ts=ts or timezone.now(),
        # account_id is an index label of the log backend, that is the
        # tenant boundary of the journal. None would reach it as the
        # literal label "None" and quietly make a bucket of its own;
        # NO_ACCOUNT is the documented value for an event that has no
        # account, a failed sign in above all.
        account_id=NO_ACCOUNT if account_id is None else account_id,
        actor=(
            actor
            or _actor_from_request(request)
            or _actor_from_context(context)
            or Actor(ActorType.SYSTEM)
        ),
        object=event_object,
        payload=normalize_payload(payload),
        workflow_id=workflow_id,
        task_id=task_id,
        ip=_from_request_or_context(get_client_ip, request, context, 'ip'),
        user_agent=_from_request_or_context(
            get_user_agent_header, request, context, 'user_agent',
        ),
        request_id=_from_request_or_context(
            _request_id, request, context, 'request_id',
        ),
    )
    event.pii = _present_pii(declared.effective_pii, event)
    return event


def reset_circuit():

    """ Forget a past failure. Used by the test fixture that keeps
        one failed write from silencing the next test. """

    _circuit.reset()


def _schedule(event: Event):

    """ Nothing is published for a rolled back transaction. """

    transaction.on_commit(lambda: _write(event))


def _write(event: Event):

    """ Catch everything on purpose. This runs as an on_commit
        callback, outside any caller's try block, and Django 2.2 pops
        callbacks off the list before calling them: an exception here
        would both return 500 for an already committed request and
        silently drop every callback registered after this one
        (attachment permissions, notifications, websocket sends).
        A missing LOGS_REDIS_URL raises EventsError from get_stream,
        a Redis outage raises RedisError or OSError. """

    now = monotonic()
    if _circuit.is_open(now):
        _circuit.dropped += 1
        return
    try:
        get_stream().xadd(event)
    except Exception as exc:  # noqa: BLE001
        _circuit.trip(now)
        _report_stream_error(exc)
        return
    if _circuit.dropped:
        logger.warning(
            'Events stream is back, events dropped meanwhile: %s',
            _circuit.dropped,
        )
        _circuit.dropped = 0


def _report_stream_error(exc: Exception) -> None:

    """ A Redis outage happens on every single request: the log line
        shows all of them, Sentry gets the throttled one. """

    logger.warning('Events stream is unavailable: %s', exc)
    report_error(
        message='Events stream is unavailable',
        data={'error': repr(exc), 'dropped': _circuit.dropped},
    )


def _actor_from_request(request) -> Optional[Actor]:
    user = getattr(request, 'user', None) if request is not None else None
    if user is None or not getattr(user, 'is_authenticated', False):
        return None
    return Actor.from_user(user, getattr(request, 'token_type', None))


def _actor_from_context(context: Optional[RequestContext]) -> Optional[Actor]:
    if context is None or context.actor_id is None:
        return None
    return Actor(
        type=context.actor_type,
        id=context.actor_id,
        email=context.actor_email,
    )


def _from_request_or_context(
    getter: Callable[[Any], Optional[str]],
    request,
    context: Optional[RequestContext],
    attr: str,
) -> Optional[str]:

    """ The request the caller handles wins over the context
        published by EventContextMiddleware. """

    if request is not None:
        value = getter(request)
        if value:
            return value
    return getattr(context, attr, None)


def _request_id(request) -> Optional[str]:

    """ Correlation id EventContextMiddleware put on the request. """

    return getattr(request, 'request_id', None)


def _present_pii(paths: Tuple[str, ...], event: Event) -> Tuple[str, ...]:

    """ Keep only the personal data the event really carries: the
        list is the audit answer to "what left the system" and must
        not name empty fields. The paths come from
        EventType.effective_pii, the one list the sink reads too. """

    return tuple(path for path in paths if _has_value(event, path))


def _has_value(event: Event, path: str) -> bool:
    head, _, tail = path.partition('.')
    if head == 'payload':
        value = event.payload.get(tail) if tail else event.payload
    elif head in ('actor', 'object'):
        holder = getattr(event, head, None)
        value = getattr(holder, tail, None) if holder else None
    elif tail:
        value = None
    else:
        value = getattr(event, head, None)
    return value is not None and value != ''
