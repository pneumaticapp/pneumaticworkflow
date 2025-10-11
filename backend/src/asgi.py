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

from django.conf import settings
from configurations import importer

importer.install()
django.setup()

from src.authentication.middleware import WebsocketAuthMiddleware
from src import urls


if configuration in {'Staging', 'Production'}:
    if settings.PROJECT_CONF['SENTRY_DSN']:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration

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
