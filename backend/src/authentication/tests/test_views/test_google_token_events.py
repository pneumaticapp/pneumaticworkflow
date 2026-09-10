import pytest
from django.contrib.auth import get_user_model

from src.accounts.enums import SourceType, UserStatus
from src.authentication.entities import UserData
from src.authentication.enums import (
    AuthTokenType,
    LoginFailedReason,
)
from src.authentication.services.google import GoogleAuthService
from src.logs.events import Actor, EventObject
from src.logs.events.emitter import NO_ACCOUNT
from src.logs.events.enums import (
    ActorType,
    EventName,
    EventObjectType,
)
from src.processes.services.system_workflows import (
    SystemWorkflowService,
)
from src.processes.tests.fixtures import create_test_owner

UserModel = get_user_model()

pytestmark = pytest.mark.django_db


def test_google_token__existent_user__emit_user_login(
    mocker,
    api_client,
    settings,
    events_enabled,
    run_on_commit,
    fake_stream,
):

    # arrange
    settings.PROJECT_CONF = {**settings.PROJECT_CONF, 'GOOGLE_AUTH': True}
    user = create_test_owner(email='sso@pneumatic.app')
    google_auth_service_init_mock = mocker.patch.object(
        GoogleAuthService,
        attribute='__init__',
        return_value=None,
    )
    get_user_data_mock = mocker.patch(
        'src.authentication.services.google.'
        'GoogleAuthService.get_user_data',
        return_value=UserData(
            email=user.email,
            first_name='John',
            last_name='Doe',
            company_name='',
            photo=None,
            job_title='',
        ),
    )
    get_auth_token_mock = mocker.patch(
        'src.authentication.services.user_auth.'
        'AuthService.get_auth_token',
        return_value='sso-token',
    )
    save_tokens_mock = mocker.patch(
        'src.authentication.services.google.'
        'GoogleAuthService.save_tokens_for_user',
    )
    update_contacts_mock = mocker.patch(
        'src.authentication.tasks.'
        'update_google_contacts.delay',
    )

    # act
    response = api_client.get(
        path='/auth/google/token',
        data={
            'code': '4/0AbUR2VMeHxU...',
            'state': 'random_state_string',
        },
        HTTP_USER_AGENT='Some/Mozilla',
        HTTP_X_REAL_IP='128.18.0.99',
        HTTP_X_REQUEST_ID='audit-google-1',
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
    assert event.payload == {'source': SourceType.GOOGLE}
    assert event.ip == '128.18.0.99'
    assert event.user_agent == 'Some/Mozilla'
    assert event.request_id == 'audit-google-1'
    google_auth_service_init_mock.assert_called_once_with()
    get_user_data_mock.assert_called_once_with(
        auth_response={
            'code': '4/0AbUR2VMeHxU...',
            'state': 'random_state_string',
        },
    )
    get_auth_token_mock.assert_called_once_with(
        user=user,
        user_agent='Some/Mozilla',
        user_ip='128.18.0.99',
    )
    save_tokens_mock.assert_called_once_with(user)
    update_contacts_mock.assert_called_once_with(user.id)


def test_google_token__new_user__emit_user_signup_only(
    mocker,
    api_client,
    identify_mock,
    group_mock,
    settings,
    events_enabled,
    run_on_commit,
    fake_stream,
):

    """ A sign up is one event: no login is reported on top of it. """

    # arrange
    settings.PROJECT_CONF = {
        **settings.PROJECT_CONF,
        'GOOGLE_AUTH': True,
        'SIGNUP': True,
    }
    google_auth_service_init_mock = mocker.patch.object(
        GoogleAuthService,
        attribute='__init__',
        return_value=None,
    )
    email = 'new_user@pneumatic.app'
    get_user_data_mock = mocker.patch(
        'src.authentication.services.google.'
        'GoogleAuthService.get_user_data',
        return_value=UserData(
            email=email,
            first_name='Jane',
            last_name='Smith',
            company_name='Test Company',
            photo=None,
            job_title='',
        ),
    )
    system_workflow_service_init_mock = mocker.patch.object(
        SystemWorkflowService,
        attribute='__init__',
        return_value=None,
    )
    create_onboarding_templates_mock = mocker.patch(
        'src.processes.services.system_workflows.'
        'SystemWorkflowService.create_onboarding_templates',
    )
    create_onboarding_workflows_mock = mocker.patch(
        'src.processes.services.system_workflows.'
        'SystemWorkflowService.create_onboarding_workflows',
    )
    create_activated_templates_mock = mocker.patch(
        'src.processes.services.system_workflows.'
        'SystemWorkflowService.create_activated_templates',
    )
    create_activated_workflows_mock = mocker.patch(
        'src.processes.services.system_workflows.'
        'SystemWorkflowService.create_activated_workflows',
    )
    account_created_mock = mocker.patch(
        'src.analysis.services.AnalyticService.account_created',
    )
    account_verified_mock = mocker.patch(
        'src.analysis.services.AnalyticService.account_verified',
    )
    get_auth_token_mock = mocker.patch(
        'src.authentication.services.user_auth.'
        'AuthService.get_auth_token',
        return_value='new-user-token',
    )
    save_tokens_mock = mocker.patch(
        'src.authentication.services.google.'
        'GoogleAuthService.save_tokens_for_user',
    )
    update_contacts_mock = mocker.patch(
        'src.authentication.tasks.'
        'update_google_contacts.delay',
    )

    # act
    response = api_client.get(
        path='/auth/google/token',
        data={
            'code': '4/0AbUR2VMeHxU...',
            'state': 'random_state_string',
        },
        HTTP_USER_AGENT='Some/Mozilla',
        HTTP_X_REAL_IP='128.18.0.99',
        HTTP_X_REQUEST_ID='audit-google-2',
    )

    # assert
    assert response.status_code == 200
    assert response.data['token'] == 'new-user-token'
    new_user = UserModel.objects.get(email=email)
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_SIGNUP
    assert event.account_id == new_user.account_id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=new_user.id,
        email=email,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=new_user.id,
    )
    assert event.payload == {'source': SourceType.GOOGLE}
    assert event.ip == '128.18.0.99'
    assert event.user_agent == 'Some/Mozilla'
    assert event.request_id == 'audit-google-2'
    google_auth_service_init_mock.assert_called_once_with()
    get_user_data_mock.assert_called_once_with(
        auth_response={
            'code': '4/0AbUR2VMeHxU...',
            'state': 'random_state_string',
        },
    )
    system_workflow_service_init_mock.assert_called_once_with(
        user=new_user,
    )
    create_onboarding_templates_mock.assert_called_once_with()
    create_onboarding_workflows_mock.assert_called_once_with()
    create_activated_templates_mock.assert_called_once_with()
    create_activated_workflows_mock.assert_called_once_with()
    identify_mock.assert_called_once_with(new_user)
    group_mock.assert_called_once_with(
        user=new_user,
        account=new_user.account,
    )
    account_created_mock.assert_called_once_with(
        user=new_user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    account_verified_mock.assert_called_once_with(
        user=new_user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    get_auth_token_mock.assert_called_once_with(
        user=new_user,
        user_agent='Some/Mozilla',
        user_ip='128.18.0.99',
    )
    save_tokens_mock.assert_called_once_with(new_user)
    update_contacts_mock.assert_called_once_with(new_user.id)


def test_google_token__inactive_user__emit_login_failed(
    mocker,
    api_client,
    settings,
):

    # arrange
    settings.PROJECT_CONF = {
        **settings.PROJECT_CONF,
        'GOOGLE_AUTH': True,
        'SIGNUP': False,
    }
    user = create_test_owner(
        email='sso@pneumatic.app',
        status=UserStatus.INACTIVE,
    )
    google_auth_service_init_mock = mocker.patch.object(
        GoogleAuthService,
        attribute='__init__',
        return_value=None,
    )
    get_user_data_mock = mocker.patch(
        'src.authentication.services.google.'
        'GoogleAuthService.get_user_data',
        return_value=UserData(
            email=user.email,
            first_name='John',
            last_name='Doe',
            company_name='',
            photo=None,
            job_title='',
        ),
    )
    get_auth_token_mock = mocker.patch(
        'src.authentication.services.user_auth.'
        'AuthService.get_auth_token',
    )
    save_tokens_mock = mocker.patch(
        'src.authentication.services.google.'
        'GoogleAuthService.save_tokens_for_user',
    )
    update_contacts_mock = mocker.patch(
        'src.authentication.tasks.'
        'update_google_contacts.delay',
    )
    emit_mock = mocker.patch('src.logs.events.services.emit')
    # sha256 of the profile address "sso@pneumatic.app": an SSO
    # callback carries no address in the body, the view passes it.
    email_hash = (
        '66b34e03de7a24e7eae47c8022412dc8a05be1e07a1b55e61686cda215e40daa'
    )

    # act
    response = api_client.get(
        path='/auth/google/token',
        data={
            'code': '4/0AbUR2VMeHxU...',
            'state': 'random_state_string',
        },
    )

    # assert
    assert response.status_code == 401
    emit_mock.assert_called_once_with(
        EventName.USER_LOGIN_FAILED,
        account_id=NO_ACCOUNT,
        actor=Actor(type=ActorType.GUEST),
        event_object=EventObject(type=EventObjectType.USER),
        payload={
            'email_hash': email_hash,
            'reason': LoginFailedReason.ACCOUNT_INACTIVE,
        },
        request=mocker.ANY,
    )
    google_auth_service_init_mock.assert_called_once_with()
    get_user_data_mock.assert_called_once_with(
        auth_response={
            'code': '4/0AbUR2VMeHxU...',
            'state': 'random_state_string',
        },
    )
    get_auth_token_mock.assert_not_called()
    save_tokens_mock.assert_not_called()
    update_contacts_mock.assert_not_called()
