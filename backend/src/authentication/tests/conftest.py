import guardian.management
import pytest
from unittest.mock import Mock

from src.generics.tests.clients import PneumaticApiClient


def pytest_configure(config):
    guardian.management.create_anonymous_user = Mock()


@pytest.fixture
def api_client():
    return PneumaticApiClient(HTTP_USER_AGENT='Mozilla/5.0')


@pytest.fixture(autouse=True)
def session_mock(mocker):
    session = mocker.patch(
        'django.contrib.sessions.backends.cache.SessionStore',
    )
    session.return_value.session_key = 'test'
    return session.return_value


@pytest.fixture
def expire_tokens_mock(mocker):
    return mocker.patch(
        'src.authentication.tokens.PneumaticToken.'
        'expire_all_tokens',
    )


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


@pytest.fixture
def verification_check_true_mock(settings):
    settings.VERIFICATION_CHECK = True
