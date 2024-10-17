import datetime
from django.utils import timezone
import pytest
from pneumatic_backend.accounts.enums import (
    BillingPlanType,
    LeaseLevel,
)
from pneumatic_backend.accounts.services.exceptions import (
    AccountServiceException,
    UserServiceException,
)
from pneumatic_backend.accounts.services import (
    AccountService,
    UserService,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_account,
)
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.processes.api_v2.services.system_workflows import (
    SystemWorkflowService
)
from pneumatic_backend.payment.stripe.service import StripeService
from pneumatic_backend.payment.stripe.exceptions import StripeServiceException
from pneumatic_backend.utils.dates import date_format


pytestmark = pytest.mark.django_db


def test_create__premium_plan__ok(
    mocker,
    api_client,
):

    # arrange
    master_account = create_test_account(plan=BillingPlanType.PREMIUM)
    master_account_owner = create_test_user(account=master_account)
    tenant_name = 'some name'
    tenant_account = create_test_account(
        name='tenant',
        tenant_name=tenant_name,
        plan=BillingPlanType.PREMIUM,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    tenant_account_owner = create_test_user(
        account=tenant_account,
        email='tenant_owner@test.test'
    )
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    account_create_mock = mocker.patch(
        'pneumatic_backend.accounts.services.AccountService.create',
        return_value=tenant_account
    )
    update_users_counts_mock = mocker.patch(
        'pneumatic_backend.accounts.services.AccountService'
        '.update_users_counts'
    )
    create_tenant_account_owner_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserService'
        '.create_tenant_account_owner',
        return_value=tenant_account_owner
    )
    sys_workflow_service_init_mock = mocker.patch.object(
        SystemWorkflowService,
        attribute='__init__',
        return_value=None
    )
    create_onboarding_templates_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService.create_onboarding_templates'
    )
    create_activated_templates_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService.create_activated_templates'
    )
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    create_off_session_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'create_off_session_subscription'
    )
    increase_plan_users_mock = mocker.patch(
        'pneumatic_backend.accounts.views.'
        'tenants.increase_plan_users.delay'
    )
    tenants_added_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'tenants_added'
    )
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.post(
        f'/tenants',
        data={
            'tenant_name': tenant_name
        }
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == tenant_account.id
    assert response.data['tenant_name'] == tenant_name
    assert response.data['date_joined'] == (
        tenant_account.date_joined.strftime(date_format)
    )
    assert response.data['date_joined_tsp'] == (
        tenant_account.date_joined.timestamp()
    )
    account_service_init_mock.assert_called_once_with(
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    user_service_init_mock.assert_called_once_with(
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    account_create_mock.assert_called_once_with(
        tenant_name=tenant_name,
        master_account=master_account,
    )
    create_tenant_account_owner_mock.assert_called_once_with(
        tenant_account=tenant_account,
        master_account=master_account
    )
    update_users_counts_mock.assert_called_once()
    sys_workflow_service_init_mock.assert_called_once_with(
        user=tenant_account_owner
    )
    create_onboarding_templates_mock.assert_called_once()
    create_activated_templates_mock.assert_called_once()
    stripe_service_init_mock.assert_not_called()
    create_off_session_subscription_mock.assert_not_called()
    increase_plan_users_mock.assert_called_once_with(
        account_id=master_account.id,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    tenants_added_mock.assert_called_once_with(
        master_user=master_account_owner,
        tenant_account=tenant_account,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )


def test_create__unlimited_plan__ok(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(plan=BillingPlanType.UNLIMITED)
    master_account_owner = create_test_user(account=master_account)
    tenant_name = 'some name'
    tenant_account = create_test_account(
        name='tenant',
        tenant_name=tenant_name,
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    tenant_account_owner = create_test_user(
        account=tenant_account,
        email='tenant_owner@test.test'
    )
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    account_create_mock = mocker.patch(
        'pneumatic_backend.accounts.services.AccountService.create',
        return_value=tenant_account
    )
    update_users_counts_mock = mocker.patch(
        'pneumatic_backend.accounts.services.AccountService'
        '.update_users_counts'
    )
    create_tenant_account_owner_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserService'
        '.create_tenant_account_owner',
        return_value=tenant_account_owner
    )
    sys_workflow_service_init_mock = mocker.patch.object(
        SystemWorkflowService,
        attribute='__init__',
        return_value=None
    )
    create_onboarding_templates_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService.create_onboarding_templates'
    )
    create_activated_templates_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService.create_activated_templates'
    )
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    create_off_session_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'create_off_session_subscription'
    )
    increase_plan_users_mock = mocker.patch(
        'pneumatic_backend.accounts.views.'
        'tenants.increase_plan_users.delay'
    )
    tenants_added_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'tenants_added'
    )
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.post(
        f'/tenants',
        data={
            'tenant_name': tenant_name
        }
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == tenant_account.id
    assert response.data['tenant_name'] == tenant_name
    assert response.data['date_joined'] == (
        tenant_account.date_joined.strftime(date_format)
    )
    assert response.data['date_joined_tsp'] == (
        tenant_account.date_joined.timestamp()
    )
    account_service_init_mock.assert_called_once_with(
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    user_service_init_mock.assert_called_once_with(
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    account_create_mock.assert_called_once_with(
        tenant_name=tenant_name,
        master_account=master_account,
    )
    create_tenant_account_owner_mock.assert_called_once_with(
        tenant_account=tenant_account,
        master_account=master_account
    )
    update_users_counts_mock.assert_called_once()
    sys_workflow_service_init_mock.assert_called_once_with(
        user=tenant_account_owner
    )
    create_onboarding_templates_mock.assert_called_once()
    create_activated_templates_mock.assert_called_once()
    increase_plan_users_mock.assert_not_called()
    stripe_service_init_mock.assert_called_once_with(
        user=master_account_owner,
        subscription_account=tenant_account,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    create_off_session_subscription_mock.assert_called_once_with(
        products=[
            {
                'code': 'unlimited_month',
                'quantity': 1
            }
        ]
    )

    tenants_added_mock.assert_called_once_with(
        master_user=master_account_owner,
        tenant_account=tenant_account,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )


def test_create__fractionalcoo__ok(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(plan=BillingPlanType.FRACTIONALCOO)
    master_account_owner = create_test_user(account=master_account)
    tenant_name = 'some name'
    tenant_account = create_test_account(
        name='tenant',
        tenant_name=tenant_name,
        plan=BillingPlanType.FRACTIONALCOO,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    tenant_account_owner = create_test_user(
        account=tenant_account,
        email='tenant_owner@test.test'
    )
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    account_create_mock = mocker.patch(
        'pneumatic_backend.accounts.services.AccountService.create',
        return_value=tenant_account
    )
    update_users_counts_mock = mocker.patch(
        'pneumatic_backend.accounts.services.AccountService'
        '.update_users_counts'
    )
    create_tenant_account_owner_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserService'
        '.create_tenant_account_owner',
        return_value=tenant_account_owner
    )
    sys_workflow_service_init_mock = mocker.patch.object(
        SystemWorkflowService,
        attribute='__init__',
        return_value=None
    )
    create_onboarding_templates_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService.create_onboarding_templates'
    )
    create_activated_templates_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService.create_activated_templates'
    )
    increase_plan_users_mock = mocker.patch(
        'pneumatic_backend.accounts.views.'
        'tenants.increase_plan_users.delay'
    )
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    create_off_session_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'create_off_session_subscription'
    )
    tenants_added_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'tenants_added'
    )
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.post(
        f'/tenants',
        data={
            'tenant_name': tenant_name
        }
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == tenant_account.id
    assert response.data['tenant_name'] == tenant_name
    assert response.data['date_joined'] == (
        tenant_account.date_joined.strftime(date_format)
    )
    assert response.data['date_joined_tsp'] == (
        tenant_account.date_joined.timestamp()
    )
    account_service_init_mock.assert_called_once_with(
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    user_service_init_mock.assert_called_once_with(
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    account_create_mock.assert_called_once_with(
        tenant_name=tenant_name,
        master_account=master_account,
    )
    create_tenant_account_owner_mock.assert_called_once_with(
        tenant_account=tenant_account,
        master_account=master_account
    )
    update_users_counts_mock.assert_called_once()
    sys_workflow_service_init_mock.assert_called_once_with(
        user=tenant_account_owner
    )
    create_onboarding_templates_mock.assert_called_once()
    create_activated_templates_mock.assert_called_once()
    stripe_service_init_mock.assert_called_once_with(
        user=master_account_owner,
        subscription_account=tenant_account,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    create_off_session_subscription_mock.assert_called_once_with(
        products=[
            {
                'code': 'unlimited_month',
                'quantity': 1
            }
        ]
    )
    increase_plan_users_mock.assert_not_called()
    tenants_added_mock.assert_called_once_with(
        master_user=master_account_owner,
        tenant_account=tenant_account,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )


def test_create__free_plan__permission_denied(
    mocker,
    api_client,
):

    # arrange
    master_account = create_test_account(plan=BillingPlanType.FREEMIUM)
    master_account_owner = create_test_user(account=master_account)
    tenant_name = 'some name'

    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None
    )
    sys_workflow_service_init_mock = mocker.patch.object(
        SystemWorkflowService,
        attribute='__init__',
        return_value=None
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.post(
        f'/tenants',
        data={
            'tenant_name': tenant_name
        }
    )

    # assert
    assert response.status_code == 403
    account_service_init_mock.assert_not_called()
    user_service_init_mock.assert_not_called()
    sys_workflow_service_init_mock.assert_not_called()


def test_create__blank_tenant_name__validation_error(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(plan=BillingPlanType.UNLIMITED)
    master_account_owner = create_test_user(account=master_account)
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None
    )
    sys_workflow_service_init_mock = mocker.patch.object(
        SystemWorkflowService,
        attribute='__init__',
        return_value=None
    )
    create_off_session_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'create_off_session_subscription'
    )
    tenants_added_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'tenants_added'
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.post(
        f'/tenants',
        data={
            'tenant_name': ''
        }
    )

    # assert
    assert response.status_code == 400
    message = 'This field may not be blank.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['name'] == 'tenant_name'
    assert response.data['message'] == message
    account_service_init_mock.assert_not_called()
    user_service_init_mock.assert_not_called()
    sys_workflow_service_init_mock.assert_not_called()
    create_off_session_subscription_mock.assert_not_called()
    tenants_added_mock.assert_not_called()


def test_create__account_service_exception__validation_error(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(plan=BillingPlanType.UNLIMITED)
    master_account_owner = create_test_user(account=master_account)
    tenant_name = 'some name'
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None
    )
    message = 'some message'
    account_create_mock = mocker.patch(
        'pneumatic_backend.accounts.services.AccountService.create',
        side_effect=AccountServiceException(message)
    )
    sys_workflow_service_init_mock = mocker.patch.object(
        SystemWorkflowService,
        attribute='__init__',
        return_value=None
    )
    create_off_session_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'create_off_session_subscription'
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.post(
        f'/tenants',
        data={
            'tenant_name': tenant_name
        }
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    account_service_init_mock.assert_called_once_with(
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    user_service_init_mock.assert_called_once_with(
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    account_create_mock.assert_called_once_with(
        tenant_name=tenant_name,
        master_account=master_account,
    )
    create_off_session_subscription_mock.assert_not_called()
    sys_workflow_service_init_mock.assert_not_called()


def test_create__stripe_service_exception__validation_error(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(plan=BillingPlanType.UNLIMITED)
    master_account_owner = create_test_user(account=master_account)
    tenant_name = 'some name'
    tenant_account = create_test_account(
        name='tenant',
        tenant_name=tenant_name,
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    tenant_account_owner = create_test_user(
        account=tenant_account,
        email='tenant_owner@test.test'
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None
    )
    mocker.patch(
        'pneumatic_backend.accounts.services.AccountService.create',
        return_value=tenant_account
    )
    mocker.patch(
        'pneumatic_backend.accounts.services.AccountService'
        '.update_users_counts'
    )
    mocker.patch(
        'pneumatic_backend.accounts.services.UserService'
        '.create_tenant_account_owner',
        return_value=tenant_account_owner
    )
    mocker.patch.object(
        SystemWorkflowService,
        attribute='__init__',
        return_value=None
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService.create_onboarding_templates'
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService.create_activated_templates'
    )
    mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    message = 'Some Error'
    create_off_session_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'create_off_session_subscription',
        side_effect=StripeServiceException(message)
    )
    tenants_added_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'tenants_added'
    )
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.post(
        f'/tenants',
        data={
            'tenant_name': tenant_name
        }
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    create_off_session_subscription_mock.assert_called_once_with(
        products=[
            {
                'code': 'unlimited_month',
                'quantity': 1
            }
        ]
    )
    tenants_added_mock.assert_not_called()


def test_create__user_service_exception__validation_error(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(plan=BillingPlanType.UNLIMITED)
    master_account_owner = create_test_user(account=master_account)
    tenant_name = 'some name'
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    tenant_account = mocker.Mock()
    account_create_mock = mocker.patch(
        'pneumatic_backend.accounts.services.AccountService.create',
        return_value=tenant_account
    )
    message = 'some message'
    user_create_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserService'
        '.create_tenant_account_owner',
        side_effect=UserServiceException(message)
    )
    sys_workflow_service_init_mock = mocker.patch.object(
        SystemWorkflowService,
        attribute='__init__',
        return_value=None
    )
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.post(
        f'/tenants',
        data={
            'tenant_name': tenant_name
        }
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    account_service_init_mock.assert_called_once_with(
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    user_service_init_mock.assert_called_once_with(
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    account_create_mock.assert_called_once_with(
        tenant_name=tenant_name,
        master_account=master_account,
    )
    user_create_mock.assert_called_once_with(
        tenant_account=tenant_account,
        master_account=master_account
    )
    sys_workflow_service_init_mock.assert_not_called()


def test_create__null_tenant_name__validation_error(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(plan=BillingPlanType.UNLIMITED)
    master_account_owner = create_test_user(account=master_account)
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None
    )
    sys_workflow_service_init_mock = mocker.patch.object(
        SystemWorkflowService,
        attribute='__init__',
        return_value=None
    )
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.post(
        f'/tenants',
        data={
            'tenant_name': None
        }
    )

    # assert
    assert response.status_code == 400
    message = 'This field may not be null.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['name'] == 'tenant_name'
    assert response.data['message'] == message
    account_service_init_mock.assert_not_called()
    user_service_init_mock.assert_not_called()
    sys_workflow_service_init_mock.assert_not_called()


def test_create__skip_tenant_name__validation_error(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(plan=BillingPlanType.UNLIMITED)
    master_account_owner = create_test_user(account=master_account)
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None
    )
    sys_workflow_service_init_mock = mocker.patch.object(
        SystemWorkflowService,
        attribute='__init__',
        return_value=None
    )
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.post(
        f'/tenants',
        data={}
    )

    # assert
    assert response.status_code == 400
    message = 'This field is required.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['name'] == 'tenant_name'
    assert response.data['message'] == message
    account_service_init_mock.assert_not_called()
    user_service_init_mock.assert_not_called()
    sys_workflow_service_init_mock.assert_not_called()


def test_create__tenant_name_over_limit__validation_error(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(plan=BillingPlanType.UNLIMITED)
    master_account_owner = create_test_user(account=master_account)
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None
    )
    sys_workflow_service_init_mock = mocker.patch.object(
        SystemWorkflowService,
        attribute='__init__',
        return_value=None
    )
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.post(
        f'/tenants',
        data={
            'tenant_name': 'a' * 256
        }
    )

    # assert
    assert response.status_code == 400
    message = 'Ensure this field has no more than 255 characters.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['name'] == 'tenant_name'
    assert response.data['message'] == message
    account_service_init_mock.assert_not_called()
    user_service_init_mock.assert_not_called()
    sys_workflow_service_init_mock.assert_not_called()


def test_create__tenant__permission_denied(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT
    )
    master_account_owner = create_test_user(account=master_account)
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    tenant_name = 'some name'
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None
    )
    sys_workflow_service_init_mock = mocker.patch.object(
        SystemWorkflowService,
        attribute='__init__',
        return_value=None
    )
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.post(
        f'/tenants',
        data={
            'tenant_name': tenant_name
        }
    )

    # assert
    assert response.status_code == 403
    account_service_init_mock.assert_not_called()
    user_service_init_mock.assert_not_called()
    sys_workflow_service_init_mock.assert_not_called()


def test_create__not_subscribed__permission_denied(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(plan=BillingPlanType.FREEMIUM)
    master_account_owner = create_test_user(account=master_account)
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    tenant_name = 'some name'
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None
    )
    sys_workflow_service_init_mock = mocker.patch.object(
        SystemWorkflowService,
        attribute='__init__',
        return_value=None
    )
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.post(
        f'/tenants',
        data={
            'tenant_name': tenant_name
        }
    )
    # assert
    assert response.status_code == 403
    account_service_init_mock.assert_not_called()
    user_service_init_mock.assert_not_called()
    sys_workflow_service_init_mock.assert_not_called()


def test_create__expired_subscription__permission_denied(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
        plan_expiration=timezone.now() - datetime.timedelta(hours=1)
    )
    master_account_owner = create_test_user(account=master_account)
    tenant_name = 'some name'
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None
    )
    sys_workflow_service_init_mock = mocker.patch.object(
        SystemWorkflowService,
        attribute='__init__',
        return_value=None
    )
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.post(
        '/tenants',
        data={
            'tenant_name': tenant_name
        }
    )

    # assert
    assert response.status_code == 403
    account_service_init_mock.assert_not_called()
    user_service_init_mock.assert_not_called()
    sys_workflow_service_init_mock.assert_not_called()


def test_create__not_admin__permission_denied(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
    )
    master_account_not_admin = create_test_user(
        account=master_account,
        is_admin=False,
        is_account_owner=False
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    tenant_name = 'some name'
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None
    )
    sys_workflow_service_init_mock = mocker.patch.object(
        SystemWorkflowService,
        attribute='__init__',
        return_value=None
    )
    api_client.token_authenticate(master_account_not_admin)

    # act
    response = api_client.post(
        f'/tenants',
        data={
            'tenant_name': tenant_name
        }
    )

    # assert
    assert response.status_code == 403
    account_service_init_mock.assert_not_called()
    user_service_init_mock.assert_not_called()
    sys_workflow_service_init_mock.assert_not_called()


def test_create__not_authenticated__auth_error(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT
    )
    create_test_user(account=master_account)
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    tenant_name = 'some name'
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None
    )
    sys_workflow_service_init_mock = mocker.patch.object(
        SystemWorkflowService,
        attribute='__init__',
        return_value=None
    )

    # act
    response = api_client.post(
        '/tenants',
        data={
            'tenant_name': tenant_name
        }
    )

    # assert
    assert response.status_code == 401
    account_service_init_mock.assert_not_called()
    user_service_init_mock.assert_not_called()
    sys_workflow_service_init_mock.assert_not_called()


@pytest.mark.parametrize('plan', BillingPlanType.PAYMENT_PLANS)
def test_create__disable_billing__skip_call_stripe(
    plan,
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(plan=plan, billing_sync=True)
    master_account_owner = create_test_user(
        account=master_account,
        is_account_owner=True
    )
    tenant_name = 'some name'
    tenant_account = create_test_account(
        name='tenant',
        tenant_name=tenant_name,
        plan=plan,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    tenant_account_owner = create_test_user(
        account=tenant_account,
        email='tenant_owner@test.test'
    )
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': False}
    account_create_mock = mocker.patch(
        'pneumatic_backend.accounts.services.AccountService.create',
        return_value=tenant_account
    )
    update_users_counts_mock = mocker.patch(
        'pneumatic_backend.accounts.services.AccountService'
        '.update_users_counts'
    )
    create_tenant_account_owner_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserService'
        '.create_tenant_account_owner',
        return_value=tenant_account_owner
    )
    sys_workflow_service_init_mock = mocker.patch.object(
        SystemWorkflowService,
        attribute='__init__',
        return_value=None
    )
    create_onboarding_templates_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService.create_onboarding_templates'
    )
    create_activated_templates_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService.create_activated_templates'
    )
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    create_off_session_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'create_off_session_subscription'
    )
    increase_plan_users_mock = mocker.patch(
        'pneumatic_backend.accounts.views.'
        'tenants.increase_plan_users.delay'
    )
    tenants_added_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'tenants_added'
    )
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.post(
        f'/tenants',
        data={
            'tenant_name': tenant_name
        }
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == tenant_account.id
    assert response.data['tenant_name'] == tenant_name
    assert response.data['date_joined']
    account_service_init_mock.assert_called_once_with(
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    user_service_init_mock.assert_called_once_with(
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    account_create_mock.assert_called_once_with(
        tenant_name=tenant_name,
        master_account=master_account,
    )
    create_tenant_account_owner_mock.assert_called_once_with(
        tenant_account=tenant_account,
        master_account=master_account
    )
    update_users_counts_mock.assert_called_once()
    sys_workflow_service_init_mock.assert_called_once_with(
        user=tenant_account_owner
    )
    create_onboarding_templates_mock.assert_called_once()
    create_activated_templates_mock.assert_called_once()
    increase_plan_users_mock.assert_not_called()
    stripe_service_init_mock.assert_not_called()
    create_off_session_subscription_mock.assert_not_called()
    tenants_added_mock.assert_called_once_with(
        master_user=master_account_owner,
        tenant_account=tenant_account,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
