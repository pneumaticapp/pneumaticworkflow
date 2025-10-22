import pytest

from src.generics.tests.clients import PneumaticApiClient


@pytest.fixture
def analysis_mock(mocker):
    return mocker.patch(
        'src.accounts.views.user_invites.AnalyticService',
    )


@pytest.fixture
def api_client():
    return PneumaticApiClient(HTTP_USER_AGENT='Mozilla/5.0')


@pytest.fixture
def identify_mock(mocker):
    return mocker.patch(
        'src.analysis.mixins.BaseIdentifyMixin.identify',
    )


@pytest.fixture
def group_mock(mocker):
    return mocker.patch(
        'src.analysis.mixins.BaseIdentifyMixin.group',
    )
