from time import monotonic
from typing import Dict, Optional, Tuple, Type

from django.conf import settings
from django.core.exceptions import DisallowedHost, PermissionDenied
from rest_framework.exceptions import (
    AuthenticationFailed,
    NotAuthenticated,
)
from sentry_sdk import capture_exception, capture_message, push_scope
from typing_extensions import Literal

# Exception types to drop in Sentry (noise: auth, infra, scan).
_SENTRY_IGNORE_EXCEPTIONS: Tuple[Type[BaseException], ...] = (
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
    DisallowedHost,
)
SENTRY_THROTTLE_SECONDS = 60
_sentry_last_messages: Dict[str, float] = {}


def sentry_before_send(event: dict, hint: dict) -> Optional[dict]:
    """Drop expected auth/validation and infra errors so they are not sent."""
    if 'exc_info' not in hint:
        return event
    _, exc_value, _ = hint['exc_info']
    if isinstance(exc_value, _SENTRY_IGNORE_EXCEPTIONS):
        return None
    return event


class SentryLogLevel:

    DEBUG = 'debug'
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    CRITICAL = 'critical'

    LITERALS = Literal[
        DEBUG,
        INFO,
        WARNING,
        ERROR,
        CRITICAL,
    ]


def capture_sentry_message(
    message: str,
    data: Optional[dict] = None,
    level: str = SentryLogLevel.WARNING,
):
    if level in (SentryLogLevel.DEBUG, SentryLogLevel.INFO):
        return
    if settings.PROJECT_CONF['SENTRY_DSN']:
        with push_scope() as scope:
            if data:
                for key, val in data.items():
                    scope.set_extra(key, val)
            capture_message(
                message=message,
                level=level,
            )


def capture_sentry_message_throttled(
    message: str,
    data: dict,
    level: SentryLogLevel.LITERALS = SentryLogLevel.ERROR,
    key: Optional[str] = None,
):
    """Send a message at most once per SENTRY_THROTTLE_SECONDS for the
    same key, the message itself by default: a repeated failure of a
    periodic job must not flood Sentry. Callers keep their own log
    line, which shows every occurrence."""
    now = monotonic()
    throttle_key = key or message
    last_sent = _sentry_last_messages.get(throttle_key)
    if last_sent is not None and now - last_sent < SENTRY_THROTTLE_SECONDS:
        return
    _sentry_last_messages[throttle_key] = now
    capture_sentry_message(
        message=message,
        data=data,
        level=level,
    )


def capture_sentry_exception(
    ex: BaseException,
    data: Optional[dict] = None,
):
    if settings.PROJECT_CONF['SENTRY_DSN']:
        with push_scope() as scope:
            if data:
                for key, val in data.items():
                    scope.set_extra(key, val)

            capture_exception(ex=ex)
