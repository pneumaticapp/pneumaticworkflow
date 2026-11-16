import pytest
from django.contrib.auth import get_user_model

from src.accounts.enums import SourceType
from src.authentication.enums import AuthTokenType
from src.processes.services.system_workflows import (
    SystemWorkflowService,
)
from src.utils.validation import ErrorCode

UserModel = get_user_model()

pytestmark = pytest.mark.django_db


def test_create__email_signup__audit_user_signed_up(
    mocker,
    api_client,
    identify_mock,
    group_mock,
    settings,
):

    # arrange
    settings.PROJECT_CONF = {**settings.PROJECT_CONF, 'SIGNUP': True}
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
    user_signed_up_mock = mocker.patch(
        'src.authentication.views.signup.AuditEventService.user_signed_up',
    )
    email = 'new_user@pneumatic.app'

    # act
    response = api_client.post(
        path='/auth/signup',
        data={'email': email},
        HTTP_USER_AGENT='Some/Mozilla',
        HTTP_X_REAL_IP='128.18.0.99',
    )

    # assert
    assert response.status_code == 200
    assert response.data['token'] == 'new-user-token'
    new_user = UserModel.objects.get(email=email)
    user_signed_up_mock.assert_called_once_with(
        user=new_user,
        source=SourceType.EMAIL,
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


def test_create__signup_disabled__audit_not_called(
    mocker,
    api_client,
    settings,
):

    # arrange
    settings.PROJECT_CONF = {**settings.PROJECT_CONF, 'SIGNUP': False}
    account_created_mock = mocker.patch(
        'src.analysis.services.AnalyticService.account_created',
    )
    user_signed_up_mock = mocker.patch(
        'src.authentication.views.signup.AuditEventService.user_signed_up',
    )
    email = 'new_user@pneumatic.app'

    # act
    response = api_client.post(
        path='/auth/signup',
        data={'email': email},
    )

    # assert
    assert response.status_code == 401
    message = 'Authentication credentials were not provided.'
    assert response.data['detail'] == message
    user_signed_up_mock.assert_not_called()
    account_created_mock.assert_not_called()


def test_create__invalid_email__audit_not_called(
    mocker,
    api_client,
    settings,
):

    # arrange
    settings.PROJECT_CONF = {**settings.PROJECT_CONF, 'SIGNUP': True}
    account_created_mock = mocker.patch(
        'src.analysis.services.AnalyticService.account_created',
    )
    user_signed_up_mock = mocker.patch(
        'src.authentication.views.signup.AuditEventService.user_signed_up',
    )
    email = 'not-an-email'

    # act
    response = api_client.post(
        path='/auth/signup',
        data={'email': email},
    )

    # assert
    assert response.status_code == 400
    message = 'Enter a valid email address.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'email'
    assert response.data['details']['reason'] == message
    user_signed_up_mock.assert_not_called()
    account_created_mock.assert_not_called()
