import guardian.management

from unittest.mock import Mock


def pytest_configure(config):
    """
    Configure pytest before tests run.
    Disable django-guardian anonymous user creation by mocking it.
    """
    # Mock guardian's create_anonymous_user function before it's imported
    guardian.management.create_anonymous_user = Mock()
