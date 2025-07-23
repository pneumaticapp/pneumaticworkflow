import pytest
from pneumatic_backend.generics.tests.clients import PneumaticApiClient


@pytest.fixture(autouse=True)
def customerio_client(mocker):
    return mocker.patch('pneumatic_backend.services.tasks.APIClient')


@pytest.fixture
def api_client():
    return PneumaticApiClient(HTTP_USER_AGENT='Mozilla/5.0')
