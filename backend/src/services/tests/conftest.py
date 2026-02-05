import guardian.management
import pytest
from unittest.mock import Mock

from src.generics.tests.clients import PneumaticApiClient


def pytest_configure(config):
    guardian.management.create_anonymous_user = Mock()


@pytest.fixture(autouse=True)
def customerio_client(mocker):
    return mocker.patch('customerio.APIClient')


@pytest.fixture
def api_client():
    return PneumaticApiClient(HTTP_USER_AGENT='Mozilla/5.0')
