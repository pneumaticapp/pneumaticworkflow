import pytest
from django.contrib.auth import get_user_model

from src.accounts.enums import SourceType, UserStatus
from src.authentication.entities import UserData
from src.authentication.enums import AuthTokenType
from src.authentication.messages import (
    MSG_AU_0003,
    MSG_AU_0009,
    MSG_AU_0016,
)
from src.authentication.services.exceptions import TokenInvalidOrExpired
from src.authentication.services.google import GoogleAuthService
from src.logs.events.enums import LoginFailedReason
from src.processes.services.system_workflows import (
    SystemWorkflowService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_owner,
)
from src.utils.validation import ErrorCode

UserModel = get_user_model()

pytestmark = pytest.mark.django_db


def test_google_token__existent_user__audit_user_logged_in(
    mocker,
    api_client,
    settings,
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
    update_google_contacts_mock = mocker.patch(
        'src.authentication.tasks.'
        'update_google_contacts.delay',
    )
    user_logged_in_mock = mocker.patch(
        'src.authentication.views.google.AuditEventService.user_logged_in',
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
    )

    # assert
    assert response.status_code == 200
    user_logged_in_mock.assert_called_once_with(
        user=user,
        source=SourceType.GOOGLE,
    )
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
    update_google_contacts_mock.assert_called_once_with(user.id)


def test_google_token__new_user__audit_user_signed_up_only(
    mocker,
    api_client,
    identify_mock,
    group_mock,
    settings,
):

    """ A sign up is one record: no login is reported on top of it. """

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
    update_google_contacts_mock = mocker.patch(
        'src.authentication.tasks.'
        'update_google_contacts.delay',
    )
    user_signed_up_mock = mocker.patch(
        'src.authentication.views.mixins.AuditEventService.user_signed_up',
    )
    user_logged_in_mock = mocker.patch(
        'src.authentication.views.google.AuditEventService.user_logged_in',
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
    )

    # assert
    assert response.status_code == 200
    assert response.data['token'] == 'new-user-token'
    new_user = UserModel.objects.get(email=email)
    user_signed_up_mock.assert_called_once_with(
        user=new_user,
        source=SourceType.GOOGLE,
    )
    user_logged_in_mock.assert_not_called()
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
    update_google_contacts_mock.assert_called_once_with(new_user.id)


def test_google_token__signup_disabled__audit_login_failed(
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
    update_google_contacts_mock = mocker.patch(
        'src.authentication.tasks.'
        'update_google_contacts.delay',
    )
    login_failed_mock = mocker.patch(
        'src.authentication.views.google.AuditEventService.login_failed',
    )
    user_logged_in_mock = mocker.patch(
        'src.authentication.views.google.AuditEventService.user_logged_in',
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
    assert response.data['detail'] == MSG_AU_0003
    login_failed_mock.assert_called_once_with(
        reason=LoginFailedReason.SIGNUP_DISABLED,
        email=user.email,
    )
    user_logged_in_mock.assert_not_called()
    google_auth_service_init_mock.assert_called_once_with()
    get_user_data_mock.assert_called_once_with(
        auth_response={
            'code': '4/0AbUR2VMeHxU...',
            'state': 'random_state_string',
        },
    )
    get_auth_token_mock.assert_not_called()
    save_tokens_mock.assert_not_called()
    update_google_contacts_mock.assert_not_called()


def test_google_token__sso_required__audit_login_failed(
    mocker,
    api_client,
    settings,
):

    """ A person who is not the owner of the account may only sign
        in through the SSO provider the deployment is set up with. """

    # arrange
    settings.PROJECT_CONF = {
        **settings.PROJECT_CONF,
        'GOOGLE_AUTH': True,
        'SSO_AUTH': True,
    }
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_admin(
        account=account,
        email='sso@pneumatic.app',
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
    update_google_contacts_mock = mocker.patch(
        'src.authentication.tasks.'
        'update_google_contacts.delay',
    )
    login_failed_mock = mocker.patch(
        'src.authentication.views.google.AuditEventService.login_failed',
    )
    user_logged_in_mock = mocker.patch(
        'src.authentication.views.google.AuditEventService.user_logged_in',
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
    assert response.status_code == 400
    assert response.data[0] == MSG_AU_0016
    login_failed_mock.assert_called_once_with(
        reason=LoginFailedReason.SSO_REQUIRED,
        email=user.email,
    )
    user_logged_in_mock.assert_not_called()
    google_auth_service_init_mock.assert_called_once_with()
    get_user_data_mock.assert_called_once_with(
        auth_response={
            'code': '4/0AbUR2VMeHxU...',
            'state': 'random_state_string',
        },
    )
    get_auth_token_mock.assert_not_called()
    save_tokens_mock.assert_not_called()
    update_google_contacts_mock.assert_not_called()


def test_google_token__save_tokens_fails__audit_not_called(
    mocker,
    api_client,
    settings,
):

    """ The login is journalled after the rest of the sign in: a
        callback that breaks on the way leaves no login behind. """

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
        side_effect=ConnectionError,
    )
    update_google_contacts_mock = mocker.patch(
        'src.authentication.tasks.'
        'update_google_contacts.delay',
    )
    user_logged_in_mock = mocker.patch(
        'src.authentication.views.google.AuditEventService.user_logged_in',
    )
    auth_response = {
        'code': '4/0AbUR2VMeHxU...',
        'state': 'random_state_string',
    }

    # act
    with pytest.raises(ConnectionError):
        api_client.get(
            path='/auth/google/token',
            data=auth_response,
            HTTP_USER_AGENT='Some/Mozilla',
            HTTP_X_REAL_IP='128.18.0.99',
        )

    # assert
    user_logged_in_mock.assert_not_called()
    google_auth_service_init_mock.assert_called_once_with()
    get_user_data_mock.assert_called_once_with(auth_response=auth_response)
    get_auth_token_mock.assert_called_once_with(
        user=user,
        user_agent='Some/Mozilla',
        user_ip='128.18.0.99',
    )
    save_tokens_mock.assert_called_once_with(user)
    update_google_contacts_mock.assert_not_called()


def test_google_token__auth_exception__audit_not_called(
    mocker,
    api_client,
    settings,
):

    # arrange
    settings.PROJECT_CONF = {**settings.PROJECT_CONF, 'GOOGLE_AUTH': True}
    google_auth_service_init_mock = mocker.patch.object(
        GoogleAuthService,
        attribute='__init__',
        return_value=None,
    )
    get_user_data_mock = mocker.patch(
        'src.authentication.services.google.'
        'GoogleAuthService.get_user_data',
        side_effect=TokenInvalidOrExpired(),
    )
    get_auth_token_mock = mocker.patch(
        'src.authentication.services.user_auth.'
        'AuthService.get_auth_token',
    )
    save_tokens_mock = mocker.patch(
        'src.authentication.services.google.'
        'GoogleAuthService.save_tokens_for_user',
    )
    update_google_contacts_mock = mocker.patch(
        'src.authentication.tasks.'
        'update_google_contacts.delay',
    )
    login_failed_mock = mocker.patch(
        'src.authentication.views.google.AuditEventService.login_failed',
    )
    user_logged_in_mock = mocker.patch(
        'src.authentication.views.google.AuditEventService.user_logged_in',
    )
    auth_response = {
        'code': '4/0AbUR2VMeHxU...',
        'state': 'random_state_string',
    }

    # act
    response = api_client.get(
        path='/auth/google/token',
        data=auth_response,
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == str(MSG_AU_0009)
    assert response.data['details'] == {}
    user_logged_in_mock.assert_not_called()
    login_failed_mock.assert_not_called()
    google_auth_service_init_mock.assert_called_once_with()
    get_user_data_mock.assert_called_once_with(auth_response=auth_response)
    get_auth_token_mock.assert_not_called()
    save_tokens_mock.assert_not_called()
    update_google_contacts_mock.assert_not_called()
