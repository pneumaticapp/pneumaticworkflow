import pytest

from src.accounts.enums import SourceType
from src.processes.tests.fixtures import create_test_owner
from src.utils.logging import SentryLogLevel

pytestmark = pytest.mark.django_db


def test_auth0_logout__authenticated__emit_logout_of_the_user(
    mocker,
    api_client,
    settings,
):

    # arrange
    settings.PROJECT_CONF = {**settings.PROJECT_CONF, 'SSO_AUTH': True}
    user = create_test_owner()
    capture_sentry_message_mock = mocker.patch(
        'src.authentication.views.auth0.capture_sentry_message',
    )
    user_logged_out_by_provider_mock = mocker.patch(
        'src.authentication.views.auth0.'
        'AuditEventService.user_logged_out_by_provider',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/auth/auth0/logout')

    # assert
    assert response.status_code == 204
    capture_sentry_message_mock.assert_called_once_with(
        message='Auth0 logout request',
        data={},
        level=SentryLogLevel.INFO,
    )
    user_logged_out_by_provider_mock.assert_called_once_with(
        target=user,
        source=SourceType.AUTH0,
    )


def test_auth0_logout__anonymous__emit_logout_without_target(
    mocker,
    api_client,
    settings,
):

    # arrange
    settings.PROJECT_CONF = {**settings.PROJECT_CONF, 'SSO_AUTH': True}
    capture_sentry_message_mock = mocker.patch(
        'src.authentication.views.auth0.capture_sentry_message',
    )
    user_logged_out_by_provider_mock = mocker.patch(
        'src.authentication.views.auth0.'
        'AuditEventService.user_logged_out_by_provider',
    )

    # act
    response = api_client.get(
        '/auth/auth0/logout',
        data={'sid': 'auth0-session-id'},
    )

    # assert
    assert response.status_code == 204
    capture_sentry_message_mock.assert_called_once_with(
        message='Auth0 logout request',
        data={'sid': ['auth0-session-id']},
        level=SentryLogLevel.INFO,
    )
    user_logged_out_by_provider_mock.assert_called_once_with(
        target=None,
        source=SourceType.AUTH0,
    )


def test_auth0_logout__sso_disabled__not_emit(
    mocker,
    api_client,
    settings,
):

    # arrange
    settings.PROJECT_CONF = {**settings.PROJECT_CONF, 'SSO_AUTH': False}
    user_logged_out_by_provider_mock = mocker.patch(
        'src.authentication.views.auth0.'
        'AuditEventService.user_logged_out_by_provider',
    )

    # act
    response = api_client.get('/auth/auth0/logout')

    # assert
    assert response.status_code == 401
    user_logged_out_by_provider_mock.assert_not_called()
