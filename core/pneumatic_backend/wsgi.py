# pylint: disable=W,C,R
"""
WSGI config for pneumatic_backend project.
It exposes the WSGI callable as a module-level variable named ``application``.
For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""
import os

configuration = os.getenv('ENVIRONMENT', 'development').title()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pneumatic_backend.settings')
os.environ.setdefault('DJANGO_CONFIGURATION', configuration)

from configurations.wsgi import get_wsgi_application
from django.conf import settings


if configuration in {'Staging', 'Production'}:
    if settings.PROJECT_CONF['SENTRY_DSN']:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        kwargs = {
            'dsn': settings.PROJECT_CONF['SENTRY_DSN'],
            'integrations': [DjangoIntegration()],
            'send_default_pii': True
        }
        if configuration == 'Production':
            kwargs['traces_sample_rate'] = 0.5
        sentry_sdk.init(**kwargs)

application = get_wsgi_application()
