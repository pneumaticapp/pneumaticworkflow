# ruff: noqa: E402
import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.sessions import CookieMiddleware, SessionMiddleware
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

configuration = os.getenv('ENVIRONMENT', 'development').title()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.settings')
os.environ.setdefault('DJANGO_CONFIGURATION', configuration)

from configurations import importer
from django.conf import settings

importer.install()
django_asgi_application = get_asgi_application()

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
        scheme = sampling_context.get('asgi_scope', {}).get('scheme')
        if scheme not in {'http', 'https'}:
            return 0
        http_method = sampling_context.get('asgi_scope', {}).get('method')
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
    'http': SentryAsgiMiddleware(django_asgi_application),
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
