import pytest

from src.generics.tests.clients import PneumaticApiClient


@pytest.fixture
def api_client():
    return PneumaticApiClient(HTTP_USER_AGENT='Mozilla/5.0')


@pytest.fixture
def analysis_mock(mocker):
    return mocker.patch(
        'src.processes.views.workflow.AnalyticService',
    )
