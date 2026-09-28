import pytest

from src.authentication.enums import AuthTokenType
from src.processes.tests.fixtures import create_test_owner

pytestmark = pytest.mark.django_db


def test_signout__user_token__audit_user_logged_out(
    mocker,
    api_client,
):

    # arrange
    user = create_test_owner()
    expire_token_mock = mocker.patch(
        'src.authentication.tokens.'
        'PneumaticToken.expire_token',
    )
    user_logged_out_mock = mocker.patch(
        'src.authentication.views.signout.AuditEventService.'
        'user_logged_out',
    )
    token = api_client.token_authenticate(user)

    # act
    response = api_client.post('/auth/signout')

    # assert
    assert response.status_code == 204
    user_logged_out_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
    )
    expire_token_mock.assert_called_once_with(token)


def test_signout__api_key__audit_api_auth_type(
    mocker,
    api_client,
):

    # arrange
    user = create_test_owner()
    expire_token_mock = mocker.patch(
        'src.authentication.tokens.'
        'PneumaticToken.expire_token',
    )
    user_logged_out_mock = mocker.patch(
        'src.authentication.views.signout.AuditEventService.'
        'user_logged_out',
    )
    api_client.token_authenticate(
        user=user,
        token_type=AuthTokenType.API,
    )

    # act
    response = api_client.post('/auth/signout')

    # assert
    assert response.status_code == 204
    user_logged_out_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.API,
    )
    expire_token_mock.assert_not_called()


def test_signout__not_authenticated__audit_not_called(
    mocker,
    api_client,
):

    # arrange
    expire_token_mock = mocker.patch(
        'src.authentication.tokens.'
        'PneumaticToken.expire_token',
    )
    user_logged_out_mock = mocker.patch(
        'src.authentication.views.signout.AuditEventService.'
        'user_logged_out',
    )

    # act
    response = api_client.post('/auth/signout')

    # assert
    assert response.status_code == 401
    user_logged_out_mock.assert_not_called()
    expire_token_mock.assert_not_called()
