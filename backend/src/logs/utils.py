import os
from contextlib import contextmanager

from django.conf import settings
from django.db import connection


@contextmanager
def log_sql():
    log_patch = os.path.join(settings.BASE_DIR, 'django_queries.log')
    open(log_patch, "w").close()  # clear from previous sql requests
    connection.force_debug_cursor = True
    yield
    connection.force_debug_cursor = False
