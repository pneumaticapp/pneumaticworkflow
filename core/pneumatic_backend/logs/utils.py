from django.db import connection
from contextlib import contextmanager


@contextmanager
def log_sql():
    open("django_queries.log", "w").close()  # clear from previous sql requests
    connection.force_debug_cursor = True
    yield
    connection.force_debug_cursor = False
