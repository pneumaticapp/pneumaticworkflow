import pytest
from pneumatic_backend.generics.tests.clients import PneumaticApiClient


@pytest.fixture
def api_client():
    return PneumaticApiClient(HTTP_USER_AGENT='Mozilla/5.0')
