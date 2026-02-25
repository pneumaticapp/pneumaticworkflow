# ruff: noqa: E402
import os

import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.sessions import CookieMiddleware, SessionMiddleware
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

from src.asgi_handler import AsgiHandler

configuration = os.getenv('ENVIRONMENT', 'development').title()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.settings')
os.environ.setdefault('DJANGO_CONFIGURATION', configuration)

from configurations import importer
from django.conf import settings

importer.install()
django.setup()

from src import urls
from src.authentication.middleware import WebsocketAuthMiddleware

if (
    configuration in {'Staging', 'Production'}
    and settings.PROJECT_CONF['SENTRY_DSN']
):
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    from src.utils.logging import sentry_before_send

    def traces_sampler(sampling_context: dict) -> float:
        scheme = sampling_context['asgi_scope']['scheme']
        if scheme not in {'http', 'https'}:
            return 0
        http_method = sampling_context['asgi_scope']['method']
        if http_method in {'HEAD', 'OPTIONS'}:
            return 0
        return 0.2

    kwargs = {
        'dsn': settings.PROJECT_CONF['SENTRY_DSN'],
        'integrations': [DjangoIntegration()],
        'send_default_pii': True,
        'traces_sampler': traces_sampler,
        'before_send': sentry_before_send,
    }
    sentry_sdk.init(**kwargs)

application = ProtocolTypeRouter({
    'http': SentryAsgiMiddleware(AsgiHandler()),
    'websocket':
        SentryAsgiMiddleware(
            CookieMiddleware(
                SessionMiddleware(
                    WebsocketAuthMiddleware(
                        URLRouter(
                            urls.websocket_urlpatterns,
                        ),
                    ),
                ),
            ),
        ),
})
