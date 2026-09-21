"""Sentry SDK initialization and event filtering for the file service."""

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from sentry_sdk.types import Event, Hint, SamplingContext

from src.shared_kernel.config import get_settings
from src.shared_kernel.exceptions import (
    AuthenticationError,
    FileAccessDeniedError,
    PermissionDeniedError,
)

_SKIP_TRACE_METHODS = frozenset({'HEAD', 'OPTIONS'})

# Exception types to drop in Sentry (noise: auth, permission checks).
_SENTRY_IGNORE_EXCEPTIONS: tuple[type[BaseException], ...] = (
    AuthenticationError,
    PermissionDeniedError,
    FileAccessDeniedError,
)


def sentry_before_send(event: Event, hint: Hint) -> Event | None:
    """Drop expected auth/permission errors so they are not sent."""
    if 'exc_info' not in hint:
        return event
    _, exc_value, _ = hint['exc_info']
    if isinstance(exc_value, _SENTRY_IGNORE_EXCEPTIONS):
        return None
    return event


def traces_sampler(sampling_context: SamplingContext) -> float:
    """Sample only real HTTP traffic, skip HEAD/OPTIONS."""
    scope = sampling_context['asgi_scope']
    # Only http scopes carry 'method'; skip anything else (e.g. lifespan).
    if scope['type'] != 'http':
        return 0
    if scope['method'] in _SKIP_TRACE_METHODS:
        return 0
    return get_settings().SENTRY_TRACES_SAMPLE_RATE


def init_sentry() -> None:
    """Initialize the Sentry SDK when SENTRY_DSN is configured."""
    settings = get_settings()
    if not settings.SENTRY_DSN:
        return

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[
            StarletteIntegration(),
            FastApiIntegration(),
        ],
        environment=settings.SENTRY_ENVIRONMENT,
        send_default_pii=True,
        traces_sampler=traces_sampler,
        before_send=sentry_before_send,
    )
