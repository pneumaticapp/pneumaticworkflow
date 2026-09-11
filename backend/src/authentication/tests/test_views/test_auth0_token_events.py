from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model

from src.accounts.enums import SourceType
from src.authentication.enums import AuthTokenType
from src.authentication.services.auth0 import Auth0Service
from src.generics.mixins.services import EncryptionMixin
from src.logs.events import Actor, EventObject
from src.logs.events.enums import (
    ActorType,
    EventName,
    EventObjectType,
)
from src.processes.tests.fixtures import (
    create_invited_user,
    create_test_owner,
)

UserModel = get_user_model()

pytestmark = pytest.mark.django_db


def test_auth0_token__existent_user__emit_user_login(
    mocker,
    api_client,
    identify_mock,
    settings,
    fake_stream,
):

    # arrange
    settings.PROJECT_CONF = {**settings.PROJECT_CONF, 'SSO_AUTH': True}
    auth0_service_init_mock = mocker.patch.object(
        Auth0Service,
        attribute='__init__',
        return_value=None,
    )
    user = create_test_owner(email='sso@pneumatic.app')
    user_data = {
        'email': user.email,
        'first_name': 'John',
        'last_name': 'Doe',
    }
    get_first_access_token_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_first_access_token',
        return_value='auth0_access_token',
    )
    get_user_profile_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_user_profile',
        return_value={'email': user.email},
    )
    get_user_data_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.get_user_data',
        return_value=user_data,
    )
    get_auth_token_mock = mocker.patch(
        'src.authentication.services.user_auth.'
        'AuthService.get_auth_token',
        return_value='sso_token',
    )
    save_tokens_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.save_tokens_for_user',
    )
    users_logged_in_mock = mocker.patch(
        'src.authentication.services.base_sso.'
        'AnalyticService.users_logged_in',
    )
    domain = 'dev-123456.auth0.com'
    state = f'{uuid4()}{EncryptionMixin.encrypt(domain)}'

    # act
    response = api_client.get(
        path='/auth/auth0/token',
        data={
            'code': '0.Ab0Aa_jrV8Qkv...9UWtS972sufQ',
            'state': state,
        },
        HTTP_USER_AGENT='Some/Mozilla',
        REMOTE_ADDR='128.18.0.99',
        HTTP_X_REQUEST_ID='audit-auth0-1',
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_LOGIN
    assert event.account_id == user.account_id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=user.id,
        email=user.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=user.id,
    )
    assert event.payload == {'source': SourceType.AUTH0}
    assert event.ip == '128.18.0.99'
    assert event.user_agent == 'Some/Mozilla'
    assert event.request_id == 'audit-auth0-1'
    auth0_service_init_mock.assert_called_once_with(domain=domain)
    get_first_access_token_mock.assert_called_once_with(
        '0.Ab0Aa_jrV8Qkv...9UWtS972sufQ',
        state,
    )
    get_user_profile_mock.assert_called_once_with('auth0_access_token')
    get_user_data_mock.assert_called_once_with({'email': user.email})
    get_auth_token_mock.assert_called_once_with(
        user=user,
        user_agent='Some/Mozilla',
        user_ip='128.18.0.99',
    )
    save_tokens_mock.assert_called_once_with(user)
    users_logged_in_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        source=SourceType.AUTH0,
    )
    identify_mock.assert_called_once_with(user)


def test_auth0_token__new_user__emit_user_signup_only(
    mocker,
    api_client,
    identify_mock,
    group_mock,
    settings,
    fake_stream,
):

    """ A sign up is one event: the login that ends the same request
        is not reported on top of it. """

    # arrange
    settings.PROJECT_CONF = {**settings.PROJECT_CONF, 'SSO_AUTH': True}
    auth0_service_init_mock = mocker.patch.object(
        Auth0Service,
        attribute='__init__',
        return_value=None,
    )
    owner = create_test_owner(email='owner@pneumatic.app')
    email = 'new_user@pneumatic.app'
    user_data = {
        'email': email,
        'first_name': 'Jane',
        'last_name': 'Smith',
    }
    identify_users_mock = mocker.patch(
        'src.accounts.services.account.identify_users.delay',
    )
    get_first_access_token_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_first_access_token',
        return_value='auth0_access_token',
    )
    get_user_profile_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_user_profile',
        return_value={'email': email},
    )
    get_user_data_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.get_user_data',
        return_value=user_data,
    )
    get_auth_token_mock = mocker.patch(
        'src.authentication.services.user_auth.'
        'AuthService.get_auth_token',
        return_value='sso_token',
    )
    save_tokens_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.save_tokens_for_user',
    )
    users_logged_in_mock = mocker.patch(
        'src.authentication.services.base_sso.'
        'AnalyticService.users_logged_in',
    )
    domain = 'dev-123456.auth0.com'
    state = f'{uuid4()}{EncryptionMixin.encrypt(domain)}'

    # act
    response = api_client.get(
        path='/auth/auth0/token',
        data={
            'code': '0.Ab0Aa_jrV8Qkv...9UWtS972sufQ',
            'state': state,
        },
        HTTP_USER_AGENT='Some/Mozilla',
        REMOTE_ADDR='128.18.0.99',
        HTTP_X_REQUEST_ID='audit-auth0-2',
    )

    # assert
    assert response.status_code == 200
    new_user = UserModel.objects.get(email=email)
    assert new_user.account_id == owner.account_id
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_SIGNUP
    assert event.account_id == owner.account_id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=new_user.id,
        email=email,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=new_user.id,
    )
    assert event.payload == {'source': SourceType.AUTH0}
    assert event.ip == '128.18.0.99'
    assert event.user_agent == 'Some/Mozilla'
    assert event.request_id == 'audit-auth0-2'
    auth0_service_init_mock.assert_called_once_with(domain=domain)
    get_first_access_token_mock.assert_called_once_with(
        '0.Ab0Aa_jrV8Qkv...9UWtS972sufQ',
        state,
    )
    get_user_profile_mock.assert_called_once_with('auth0_access_token')
    get_user_data_mock.assert_called_once_with({'email': email})
    get_auth_token_mock.assert_called_once_with(
        user=new_user,
        user_agent='Some/Mozilla',
        user_ip='128.18.0.99',
    )
    save_tokens_mock.assert_called_once_with(new_user)
    users_logged_in_mock.assert_called_once_with(
        user=new_user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        source=SourceType.AUTH0,
    )
    # Once by the user service that created the person, once by the view.
    assert identify_mock.call_count == 2
    identify_mock.assert_has_calls(
        [mocker.call(new_user), mocker.call(new_user)],
    )
    identify_users_mock.assert_called_once_with(
        user_ids=(owner.id, new_user.id),
    )
    group_mock.assert_called_once_with(
        user=new_user,
        account=owner.account,
    )


def test_auth0_token__invited_user__emit_user_login(
    mocker,
    api_client,
    identify_mock,
    settings,
):

    # arrange
    settings.PROJECT_CONF = {**settings.PROJECT_CONF, 'SSO_AUTH': True}
    auth0_service_init_mock = mocker.patch.object(
        Auth0Service,
        attribute='__init__',
        return_value=None,
    )
    owner = create_test_owner(email='owner@pneumatic.app')
    invited_user = create_invited_user(
        user=owner,
        email='invited@pneumatic.app',
    )
    user_data = {
        'email': invited_user.email,
        'first_name': 'Invited',
        'last_name': 'User',
    }
    get_first_access_token_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_first_access_token',
        return_value='auth0_access_token',
    )
    get_user_profile_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_user_profile',
        return_value={'email': invited_user.email},
    )
    get_user_data_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.get_user_data',
        return_value=user_data,
    )
    activate_invited_user_mock = mocker.patch(
        'src.authentication.services.base_sso.'
        'BaseSSOService._activate_invited_user',
        return_value=invited_user,
    )
    get_auth_token_mock = mocker.patch(
        'src.authentication.services.user_auth.'
        'AuthService.get_auth_token',
        return_value='sso_token',
    )
    save_tokens_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.save_tokens_for_user',
    )
    users_logged_in_mock = mocker.patch(
        'src.authentication.services.base_sso.'
        'AnalyticService.users_logged_in',
    )
    emit_mock = mocker.patch('src.logs.events.services.emit')
    domain = 'dev-123456.auth0.com'
    state = f'{uuid4()}{EncryptionMixin.encrypt(domain)}'

    # act
    response = api_client.get(
        path='/auth/auth0/token',
        data={
            'code': '0.Ab0Aa_jrV8Qkv...9UWtS972sufQ',
            'state': state,
        },
        HTTP_USER_AGENT='Some/Mozilla',
        REMOTE_ADDR='128.18.0.99',
    )

    # assert
    assert response.status_code == 200
    emit_mock.assert_called_once_with(
        EventName.USER_LOGIN,
        account_id=invited_user.account_id,
        actor=Actor(
            type=ActorType.USER,
            id=invited_user.id,
            email=invited_user.email,
        ),
        event_object=EventObject(
            type=EventObjectType.USER,
            id=invited_user.id,
        ),
        payload={'source': SourceType.AUTH0},
        request=mocker.ANY,
    )
    auth0_service_init_mock.assert_called_once_with(domain=domain)
    get_first_access_token_mock.assert_called_once_with(
        '0.Ab0Aa_jrV8Qkv...9UWtS972sufQ',
        state,
    )
    get_user_profile_mock.assert_called_once_with('auth0_access_token')
    get_user_data_mock.assert_called_once_with(
        {'email': invited_user.email},
    )
    activate_invited_user_mock.assert_called_once_with(
        invited_user,
        user_data,
    )
    get_auth_token_mock.assert_called_once_with(
        user=invited_user,
        user_agent='Some/Mozilla',
        user_ip='128.18.0.99',
    )
    save_tokens_mock.assert_called_once_with(invited_user)
    users_logged_in_mock.assert_called_once_with(
        user=invited_user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        source=SourceType.AUTH0,
    )
    identify_mock.assert_called_once_with(invited_user)
