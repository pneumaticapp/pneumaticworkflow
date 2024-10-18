import os
import firebase_admin
from datetime import timedelta
from contextlib import contextmanager
from celery import Celery
from typing import Optional
from django.core.cache import cache
from django.conf import settings
from configurations import importer
from django.utils import timezone

configuration = os.getenv('ENVIRONMENT', 'Development').title()
os.environ.setdefault('DJANGO_CONFIGURATION', configuration)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pneumatic_backend.settings')

importer.install()

celery_config = {}

# Env vars not exists for "Testing" and "Development" env
if configuration in (
    settings.CONFIGURATION_STAGING,
    settings.CONFIGURATION_PROD
):
    kwargs = {}
    if settings.PROJECT_CONF['SENTRY_DSN']:
        import sentry_sdk
        from sentry_sdk.integrations.celery import CeleryIntegration
        kwargs = {
            'dsn': settings.PROJECT_CONF['SENTRY_DSN'],
            'integrations': [CeleryIntegration()],
            'send_default_pii': True
        }
        if configuration == settings.CONFIGURATION_PROD:
            kwargs['traces_sample_rate'] = 0.5
        sentry_sdk.init(**kwargs)

    if settings.PROJECT_CONF['PUSH']:
        path_firebase_credentials = os.getenv(
            'FIREBASE_PUSH_APPLICATION_CREDENTIALS'
        )
        cred = firebase_admin.credentials.Certificate(
            path_firebase_credentials
        )
        firebase_admin.initialize_app(cred)
    celery_config['broker'] = settings.CELERY_BROKER_URL

celery_app = Celery(
    'pneumatic_backend',
    **celery_config
)
celery_app.conf.setdefault('broker_login_method', 'PLAIN')
celery_app.config_from_object('django.conf:settings')


default_lock_expire = 60 * 10  # Lock expires in 10 minutes


@contextmanager
def periodic_lock(
    lock_id: str,
    lock_expire: Optional[int] = None
):

    """ Ensuring a periodic task is only executed one at a time
        https://docs.celeryq.dev/en/stable/tutorials/task-cookbook.html """

    lock_expire = lock_expire or default_lock_expire
    timeout_at = timezone.now() + timedelta(seconds=lock_expire)
    status = cache.add(lock_id, celery_app.oid, lock_expire)
    try:
        yield status
    finally:
        if timezone.now() < timeout_at and status:
            cache.delete(lock_id)
