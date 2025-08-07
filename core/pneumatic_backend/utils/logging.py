from typing import Optional
from django.conf import settings
from typing_extensions import Literal
from sentry_sdk import capture_message, push_scope, capture_exception


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

    if settings.PROJECT_CONF['SENTRY_DSN']:
        with push_scope() as scope:
            if data:
                for key, val in data.items():
                    scope.set_extra(key, val)
            capture_message(
                message=message,
                level=level
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
