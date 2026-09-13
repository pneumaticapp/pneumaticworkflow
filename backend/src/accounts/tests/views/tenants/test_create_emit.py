import pytest

from src.accounts.enums import BillingPlanType, LeaseLevel
from src.accounts.messages import MSG_A_0025
from src.accounts.services.account import AccountService
from src.accounts.services.exceptions import AccountServiceException
from src.accounts.services.user import UserService
from src.authentication.enums import AuthTokenType
from src.logs.events.enums import (
    ActorType,
    EventCategory,
    EventName,
    EventObjectType,
)
from src.logs.events.schema import Actor, EventObject
from src.payment.messages import MSG_BL_0008
from src.payment.stripe.exceptions import CardError
from src.payment.stripe.service import StripeService
from src.processes.services.system_workflows import SystemWorkflowService
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_create__free_plan__emit_tenant_create_in_master_account(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    master_account = create_test_account(plan=BillingPlanType.FREEMIUM)
    master_owner = create_test_owner(account=master_account)
    tenant_account = create_test_account(
        name='tenant',
        tenant_name='Tenant name',
        plan=BillingPlanType.FREEMIUM,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account,
    )
    tenant_owner = create_test_owner(
        account=tenant_account,
        email='tenant_owner@test.test',
    )
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None,
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    account_create_mock = mocker.patch(
        'src.accounts.services.account.AccountService.create',
        return_value=tenant_account,
    )
    update_users_counts_mock = mocker.patch(
        'src.accounts.services.account.AccountService.update_users_counts',
    )
    create_tenant_account_owner_mock = mocker.patch(
        'src.accounts.services.user.UserService.create_tenant_account_owner',
        return_value=tenant_owner,
    )
    sys_workflow_service_init_mock = mocker.patch.object(
        SystemWorkflowService,
        attribute='__init__',
        return_value=None,
    )
    create_onboarding_templates_mock = mocker.patch(
        'src.processes.services.system_workflows.'
        'SystemWorkflowService.create_onboarding_templates',
    )
    create_activated_templates_mock = mocker.patch(
        'src.processes.services.system_workflows.'
        'SystemWorkflowService.create_activated_templates',
    )
    increase_plan_users_mock = mocker.patch(
        'src.accounts.views.tenants.increase_plan_users.delay',
    )
    tenants_added_mock = mocker.patch(
        'src.analysis.services.AnalyticService.tenants_added',
    )
    api_client.token_authenticate(
        master_owner,
        user_agent='Chrome/141',
        user_ip='10.10.0.12',
    )

    # act
    response = api_client.post(
        '/tenants',
        data={'tenant_name': 'Tenant name'},
        format='json',
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.TENANT_CREATE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == master_account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=master_owner.id,
        email=master_owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.ACCOUNT,
        id=tenant_account.id,
    )
    assert event.payload == {
        'name': 'Tenant name',
        'billing_plan': BillingPlanType.FREEMIUM,
    }
    assert event.ip == '10.10.0.12'
    assert event.user_agent == 'Chrome/141'
    assert event.pii == ('actor.email', 'ip', 'user_agent', 'payload.name')
    account_service_init_mock.assert_called_once_with(
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    user_service_init_mock.assert_called_once_with(
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    account_create_mock.assert_called_once_with(
        tenant_name='Tenant name',
        master_account=master_account,
    )
    update_users_counts_mock.assert_called_once_with()
    create_tenant_account_owner_mock.assert_called_once_with(
        tenant_account=tenant_account,
        master_account=master_account,
    )
    sys_workflow_service_init_mock.assert_called_once_with(user=tenant_owner)
    create_onboarding_templates_mock.assert_called_once_with()
    create_activated_templates_mock.assert_called_once_with()
    increase_plan_users_mock.assert_not_called()
    tenants_added_mock.assert_called_once_with(
        master_user=master_owner,
        tenant_account=tenant_account,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )


def test_create__account_service_exception__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    master_account = create_test_account(plan=BillingPlanType.UNLIMITED)
    master_owner = create_test_owner(account=master_account)
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None,
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    account_create_mock = mocker.patch(
        'src.accounts.services.account.AccountService.create',
        side_effect=AccountServiceException(MSG_A_0025),
    )
    increase_plan_users_mock = mocker.patch(
        'src.accounts.views.tenants.increase_plan_users.delay',
    )
    tenants_added_mock = mocker.patch(
        'src.analysis.services.AnalyticService.tenants_added',
    )
    api_client.token_authenticate(master_owner)

    # act
    response = api_client.post(
        '/tenants',
        data={'tenant_name': 'Tenant name'},
        format='json',
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_A_0025
    assert response.data['details'] == {}
    assert fake_stream.events == []
    account_service_init_mock.assert_called_once_with(
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    user_service_init_mock.assert_called_once_with(
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    account_create_mock.assert_called_once_with(
        tenant_name='Tenant name',
        master_account=master_account,
    )
    increase_plan_users_mock.assert_not_called()
    tenants_added_mock.assert_not_called()


def test_create__stripe_exception__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    master_account = create_test_account(plan=BillingPlanType.UNLIMITED)
    master_owner = create_test_owner(account=master_account)
    tenant_account = create_test_account(
        name='tenant',
        tenant_name='Tenant name',
        plan=None,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account,
    )
    tenant_owner = create_test_owner(
        account=tenant_account,
        email='tenant_owner@test.test',
    )
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None,
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    account_create_mock = mocker.patch(
        'src.accounts.services.account.AccountService.create',
        return_value=tenant_account,
    )
    update_users_counts_mock = mocker.patch(
        'src.accounts.services.account.AccountService.update_users_counts',
    )
    create_tenant_account_owner_mock = mocker.patch(
        'src.accounts.services.user.UserService.create_tenant_account_owner',
        return_value=tenant_owner,
    )
    sys_workflow_service_init_mock = mocker.patch.object(
        SystemWorkflowService,
        attribute='__init__',
        return_value=None,
    )
    create_onboarding_templates_mock = mocker.patch(
        'src.processes.services.system_workflows.'
        'SystemWorkflowService.create_onboarding_templates',
    )
    create_activated_templates_mock = mocker.patch(
        'src.processes.services.system_workflows.'
        'SystemWorkflowService.create_activated_templates',
    )
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    create_off_session_subscription_mock = mocker.patch(
        'src.payment.stripe.service.StripeService.'
        'create_off_session_subscription',
        side_effect=CardError(),
    )
    increase_plan_users_mock = mocker.patch(
        'src.accounts.views.tenants.increase_plan_users.delay',
    )
    tenants_added_mock = mocker.patch(
        'src.analysis.services.AnalyticService.tenants_added',
    )
    api_client.token_authenticate(master_owner)

    # act
    response = api_client.post(
        '/tenants',
        data={'tenant_name': 'Tenant name'},
        format='json',
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_BL_0008
    assert response.data['details'] == {}
    assert fake_stream.events == []
    account_service_init_mock.assert_called_once_with(
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    user_service_init_mock.assert_called_once_with(
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    account_create_mock.assert_called_once_with(
        tenant_name='Tenant name',
        master_account=master_account,
    )
    update_users_counts_mock.assert_called_once_with()
    create_tenant_account_owner_mock.assert_called_once_with(
        tenant_account=tenant_account,
        master_account=master_account,
    )
    sys_workflow_service_init_mock.assert_called_once_with(
        user=tenant_owner,
    )
    create_onboarding_templates_mock.assert_called_once_with()
    create_activated_templates_mock.assert_called_once_with()
    stripe_service_init_mock.assert_called_once_with(
        user=master_owner,
        subscription_account=tenant_account,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_off_session_subscription_mock.assert_called_once_with(
        products=[{'code': 'unlimited_month', 'quantity': 1}],
    )
    increase_plan_users_mock.assert_not_called()
    tenants_added_mock.assert_not_called()
