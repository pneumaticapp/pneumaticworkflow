import pytest
from pneumatic_backend.generics.tests.clients import PneumaticApiClient


@pytest.fixture
def analytics_mock(mocker):
    return mocker.patch(
        'pneumatic_backend.accounts.views.user_invites.AnalyticService',
    )


@pytest.fixture(autouse=True)
def session_mock(mocker):
    session = mocker.patch(
        'django.contrib.sessions.backends.cache.SessionStore',
    )
    session.return_value.session_key = 'test'


@pytest.fixture
def api_client():
    return PneumaticApiClient(HTTP_USER_AGENT='Mozilla/5.0')


@pytest.fixture
def identify_mock(mocker):
    return mocker.patch(
        'pneumatic_backend.analytics.mixins.BaseIdentifyMixin.identify'
    )


@pytest.fixture
def group_mock(mocker):
    return mocker.patch(
        'pneumatic_backend.analytics.mixins.BaseIdentifyMixin.group'
    )


@pytest.fixture(autouse=True)
def push_service_mock(mocker):
    return mocker.patch(
        'pneumatic_backend.notifications.tasks.'
        'PushNotificationService',
    )
