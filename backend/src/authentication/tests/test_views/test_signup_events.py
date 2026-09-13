import pytest
from django.contrib.auth import get_user_model

from src.accounts.enums import SourceType
from src.authentication.enums import AuthTokenType
from src.logs.events.schema import Actor, EventObject
from src.logs.events.enums import (
    ActorType,
    EventCategory,
    EventName,
    EventObjectType,
)
from src.processes.services.system_workflows import (
    SystemWorkflowService,
)

UserModel = get_user_model()

pytestmark = pytest.mark.django_db


def test_create__email_signup__emit_user_signup_only(
    mocker,
    api_client,
    identify_mock,
    group_mock,
    settings,
    fake_stream,
):

    """ A sign up is one event: no login is reported on top of it,
        and the request of the sign up form is the source of the
        address and the browser. """

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
    email = 'new_user@pneumatic.app'

    # act
    response = api_client.post(
        path='/auth/signup',
        data={'email': email},
        HTTP_USER_AGENT='Some/Mozilla',
        HTTP_X_REAL_IP='128.18.0.99',
        HTTP_X_REQUEST_ID='audit-signup-1',
    )

    # assert
    assert response.status_code == 200
    assert response.data['token'] == 'new-user-token'
    new_user = UserModel.objects.get(email=email)
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_SIGNUP
    assert event.category == EventCategory.AUDIT
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
    assert event.payload == {'source': SourceType.EMAIL}
    assert event.ip == '128.18.0.99'
    assert event.user_agent == 'Some/Mozilla'
    assert event.request_id == 'audit-signup-1'
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
