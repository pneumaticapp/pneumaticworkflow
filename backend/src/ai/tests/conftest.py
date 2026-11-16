import socket

import pytest
from src.generics.tests.clients import PneumaticApiClient


@pytest.fixture
def api_client():
    return PneumaticApiClient(HTTP_USER_AGENT='Mozilla/5.0')


@pytest.fixture(autouse=True)
def getaddrinfo_mock(mocker):
    return mocker.patch(
        'src.ai.serializers.socket.getaddrinfo',
        return_value=[
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('8.8.8.8', 0)),
        ],
    )
