import guardian.management
from unittest.mock import Mock


def pytest_configure(config):
    # Guardian creates an AnonymousUser on post_migrate; the custom
    # User model has no such row, so the hook is disabled for tests
    # (same as in the other apps' conftest).
    guardian.management.create_anonymous_user = Mock()
