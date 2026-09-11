import pytest

from src.accounts.enums import SourceType
from src.authentication.enums import AuthTokenType
from src.authentication.services.auth0 import Auth0Service
from src.processes.tests.fixtures import (
    create_invited_user,
    create_test_account,
    create_test_not_admin,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_complete_authentication__active_user__login_published(mocker):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    auth0_service_init_mock = mocker.patch.object(
        Auth0Service,
        attribute='__init__',
        return_value=None,
    )
    get_auth_token_mock = mocker.patch(
        'src.authentication.services.user_auth.AuthService.get_auth_token',
        return_value='token',
    )
    save_tokens_for_user_mock = mocker.patch.object(
        Auth0Service,
        attribute='save_tokens_for_user',
    )
    users_logged_in_mock = mocker.patch(
        'src.authentication.services.base_sso.AnalyticService'
        '.users_logged_in',
    )
    user_logged_in_mock = mocker.patch(
        'src.authentication.services.base_sso.AuditEventService'
        '.user_logged_in',
    )
    service = Auth0Service()
    user_data = {'email': user.email}

    # act
    result = service._complete_authentication(
        user_data=user_data,
        user_agent='Mozilla/5.0',
        user_ip='10.0.0.1',
    )

    # assert
    assert result == (user, 'token')
    auth0_service_init_mock.assert_called_once_with()
    get_auth_token_mock.assert_called_once_with(
        user=user,
        user_agent='Mozilla/5.0',
        user_ip='10.0.0.1',
    )
    save_tokens_for_user_mock.assert_called_once_with(user)
    users_logged_in_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        source=SourceType.AUTH0,
    )
    user_logged_in_mock.assert_called_once_with(
        user=user,
        source=SourceType.AUTH0,
    )


def test_complete_authentication__invited_user__login_published(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    invited = create_invited_user(user=owner)
    auth0_service_init_mock = mocker.patch.object(
        Auth0Service,
        attribute='__init__',
        return_value=None,
    )
    activate_invited_user_mock = mocker.patch.object(
        Auth0Service,
        attribute='_activate_invited_user',
        return_value=invited,
    )
    get_auth_token_mock = mocker.patch(
        'src.authentication.services.user_auth.AuthService.get_auth_token',
        return_value='token',
    )
    save_tokens_for_user_mock = mocker.patch.object(
        Auth0Service,
        attribute='save_tokens_for_user',
    )
    users_logged_in_mock = mocker.patch(
        'src.authentication.services.base_sso.AnalyticService'
        '.users_logged_in',
    )
    user_logged_in_mock = mocker.patch(
        'src.authentication.services.base_sso.AuditEventService'
        '.user_logged_in',
    )
    service = Auth0Service()
    user_data = {'email': invited.email}

    # act
    result = service._complete_authentication(
        user_data=user_data,
        user_agent='Mozilla/5.0',
        user_ip='10.0.0.1',
    )

    # assert
    assert result == (invited, 'token')
    auth0_service_init_mock.assert_called_once_with()
    activate_invited_user_mock.assert_called_once_with(
        invited,
        user_data,
    )
    get_auth_token_mock.assert_called_once_with(
        user=invited,
        user_agent='Mozilla/5.0',
        user_ip='10.0.0.1',
    )
    save_tokens_for_user_mock.assert_called_once_with(invited)
    users_logged_in_mock.assert_called_once_with(
        user=invited,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        source=SourceType.AUTH0,
    )
    user_logged_in_mock.assert_called_once_with(
        user=invited,
        source=SourceType.AUTH0,
    )


def test_complete_authentication__new_user__no_login_published(mocker):

    """ A person this call creates is journalled as a sign up
        by after_signup; a login on top of it would count one
        arrival twice. """

    # arrange
    account = create_test_account()
    created = create_test_not_admin(account=account)
    auth0_service_init_mock = mocker.patch.object(
        Auth0Service,
        attribute='__init__',
        return_value=None,
    )
    create_new_user_mock = mocker.patch.object(
        Auth0Service,
        attribute='_create_new_user',
        return_value=created,
    )
    get_auth_token_mock = mocker.patch(
        'src.authentication.services.user_auth.AuthService.get_auth_token',
        return_value='token',
    )
    save_tokens_for_user_mock = mocker.patch.object(
        Auth0Service,
        attribute='save_tokens_for_user',
    )
    users_logged_in_mock = mocker.patch(
        'src.authentication.services.base_sso.AnalyticService'
        '.users_logged_in',
    )
    user_logged_in_mock = mocker.patch(
        'src.authentication.services.base_sso.AuditEventService'
        '.user_logged_in',
    )
    service = Auth0Service()
    user_data = {'email': 'nobody@test.test'}

    # act
    result = service._complete_authentication(
        user_data=user_data,
        user_agent='Mozilla/5.0',
        user_ip='10.0.0.1',
    )

    # assert
    assert result == (created, 'token')
    auth0_service_init_mock.assert_called_once_with()
    create_new_user_mock.assert_called_once_with(user_data)
    get_auth_token_mock.assert_called_once_with(
        user=created,
        user_agent='Mozilla/5.0',
        user_ip='10.0.0.1',
    )
    save_tokens_for_user_mock.assert_called_once_with(created)
    users_logged_in_mock.assert_called_once_with(
        user=created,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        source=SourceType.AUTH0,
    )
    user_logged_in_mock.assert_not_called()
