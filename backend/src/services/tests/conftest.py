import pytest

from src.generics.tests.clients import PneumaticApiClient


@pytest.fixture(autouse=True)
def customerio_client(mocker):
    return mocker.patch('customerio.APIClient')


@pytest.fixture
def api_client():
    return PneumaticApiClient(HTTP_USER_AGENT='Mozilla/5.0')
