import guardian.management
import pytest
from unittest.mock import Mock

from src.generics.tests.clients import PneumaticApiClient

from src.logs.events.tests.conftest import (  # noqa: F401
    events_enabled,
    fake_stream,
    run_on_commit,
)


def pytest_configure(config):
    guardian.management.create_anonymous_user = Mock()


@pytest.fixture
def api_client():
    return PneumaticApiClient(HTTP_USER_AGENT='Mozilla/5.0')
