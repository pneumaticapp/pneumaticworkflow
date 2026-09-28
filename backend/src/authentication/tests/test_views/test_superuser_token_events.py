import pytest

from src.authentication.enums import AuthTokenType
from src.processes.tests.fixtures import create_test_owner

pytestmark = pytest.mark.django_db


def test_superuser_token__ok__audit_superuser_logged_in_as(
    mocker,
    api_client,
):

    # arrange
    superuser = create_test_owner(email='superuser@pneumatic.app')
    superuser.is_superuser = True
    superuser.save(update_fields=['is_superuser'])
    target_user = create_test_owner(email='client@pneumatic.app')
    get_superuser_auth_token_mock = mocker.patch(
        'src.authentication.views.signin.AuthService.'
        'get_superuser_auth_token',
        return_value='NeverGonnaGiveYouUpNeverGonnaLet',
    )
    superuser_logged_in_as_mock = mocker.patch(
        'src.authentication.views.signin.AuditEventService.'
        'superuser_logged_in_as',
    )
    api_client.token_authenticate(superuser)

    # act
    response = api_client.post(
        path='/auth/superuser/token',
        data={'email': target_user.email},
    )

    # assert
    assert response.status_code == 200
    superuser_logged_in_as_mock.assert_called_once_with(
        user=superuser,
        auth_type=AuthTokenType.USER,
        target=target_user,
    )
    get_superuser_auth_token_mock.assert_called_once_with(target_user)


def test_superuser_token__not_superuser__audit_not_called(
    mocker,
    api_client,
):

    # arrange
    user = create_test_owner(email='regular@pneumatic.app')
    target_user = create_test_owner(email='client@pneumatic.app')
    get_superuser_auth_token_mock = mocker.patch(
        'src.authentication.views.signin.AuthService.'
        'get_superuser_auth_token',
    )
    superuser_logged_in_as_mock = mocker.patch(
        'src.authentication.views.signin.AuditEventService.'
        'superuser_logged_in_as',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path='/auth/superuser/token',
        data={'email': target_user.email},
    )

    # assert
    assert response.status_code == 403
    superuser_logged_in_as_mock.assert_not_called()
    get_superuser_auth_token_mock.assert_not_called()


def test_superuser_token__unknown_email__audit_not_called(
    mocker,
    api_client,
):

    # arrange
    superuser = create_test_owner(email='superuser@pneumatic.app')
    superuser.is_superuser = True
    superuser.save(update_fields=['is_superuser'])
    get_superuser_auth_token_mock = mocker.patch(
        'src.authentication.views.signin.AuthService.'
        'get_superuser_auth_token',
    )
    superuser_logged_in_as_mock = mocker.patch(
        'src.authentication.views.signin.AuditEventService.'
        'superuser_logged_in_as',
    )
    api_client.token_authenticate(superuser)

    # act
    response = api_client.post(
        path='/auth/superuser/token',
        data={'email': 'unknown@pneumatic.app'},
    )

    # assert
    assert response.status_code == 404
    superuser_logged_in_as_mock.assert_not_called()
    get_superuser_auth_token_mock.assert_not_called()
