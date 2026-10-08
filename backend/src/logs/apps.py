from urllib.parse import urlsplit

from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from src.logs.enums import LogsBackend

LOGS_URL_SCHEMES = (
    ('LOGS_REDIS_URL', ('redis', 'rediss', 'unix')),
    ('LOGS_OTLP_ENDPOINT', ('http', 'https')),
)
LOGS_POSITIVE_INTS = ('LOGS_STREAM_MAXLEN', 'LOGS_CONSUMER_BATCH_SIZE')


class LogsConfig(AppConfig):
    name = 'src.logs'

    def ready(self):
        """An enabled journal with an incomplete or invalid configuration
        refuses to start the web and the celery processes, before the
        first event is emitted or consumed."""
        if not settings.LOGS_BACKEND:
            return
        if settings.LOGS_BACKEND not in LogsBackend.VALUES:
            raise ImproperlyConfigured('Invalid LOGS_BACKEND')
        for name, schemes in LOGS_URL_SCHEMES:
            value = getattr(settings, name, None)
            if not isinstance(value, str):
                raise ImproperlyConfigured(f'Invalid or missing {name}')
            try:
                url = urlsplit(value)
                valid = (
                    url.scheme in schemes
                    and (url.hostname or (url.scheme == 'unix' and url.path))
                    and (url.port is None or url.port > 0)
                )
            except ValueError:
                valid = False
            if name == 'LOGS_OTLP_ENDPOINT':
                valid = valid and '?' not in value and '#' not in value
            if not valid:
                raise ImproperlyConfigured(f'Invalid or missing {name}')
        for name in LOGS_POSITIVE_INTS:
            value = getattr(settings, name, None)
            if type(value) is not int or value <= 0:
                raise ImproperlyConfigured(f'Invalid or missing {name}')
