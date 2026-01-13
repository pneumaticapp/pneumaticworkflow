import logging
from typing import Optional

from django.conf import settings
from sentry_sdk import capture_exception, capture_message, push_scope
from typing_extensions import Literal


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
                level=level,
            )


def get_okta_logout_logger():
    logger = logging.getLogger('okta_logout')

    if not logger.handlers:
        handler = logging.FileHandler('okta_logout.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

    return logger


def log_okta_message(
    message: str,
    data: Optional[dict] = None,
    level: str = SentryLogLevel.INFO,
    logger_name: str = 'okta_logout',
):
    if settings.PROJECT_CONF.get('SENTRY_DSN'):
        try:
            capture_sentry_message(message, data, level)
            return
        except Exception:  # noqa: BLE001
            pass

    logger = logging.getLogger(logger_name)

    if not logger.handlers:
        handler = logging.FileHandler(f'{logger_name}.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

    log_message = message
    if data:
        log_message += f" | Data: {data}"

    if level == SentryLogLevel.DEBUG:
        logger.debug(log_message)
    elif level == SentryLogLevel.INFO:
        logger.info(log_message)
    elif level == SentryLogLevel.WARNING:
        logger.warning(log_message)
    elif level == SentryLogLevel.ERROR:
        logger.error(log_message)
    elif level == SentryLogLevel.CRITICAL:
        logger.critical(log_message)
    else:
        logger.info(log_message)


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
