# pylint: disable=protected-access
import pytest
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from pneumatic_backend.processes.tests.fixtures import (
    create_test_account,
    create_test_user
)
from pneumatic_backend.accounts.enums import (
    BillingPlanType,
    LeaseLevel,
)
from pneumatic_backend.payment.tasks import _increase_plan_users
from pneumatic_backend.payment.stripe.exceptions import (
    StripeServiceException
)
from pneumatic_backend.payment.stripe.service import (
    StripeService
)
from pneumatic_backend.authentication.enums import AuthTokenType


UserModel = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('lease_level', LeaseLevel.NOT_TENANT_LEVELS)
def test__increment__ok(lease_level, mocker):

    # arrange
    account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        lease_level=lease_level,
        max_users=2
    )
    quantity = 3
    is_superuser = False
    auth_type = AuthTokenType.USER

    user = create_test_user(
        account=account,
        is_account_owner=True,
        email='master@test.test'
    )
    get_paid_users_count_mock = mocker.patch(
        'pneumatic_backend.accounts.models.Account.'
        'get_paid_users_count',
        return_value=4
    )
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    increase_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService.increase_subscription'
    )

    # act
    _increase_plan_users(
        account_id=account.id,
        is_superuser=is_superuser,
        auth_type=auth_type
    )

    # assert
    get_paid_users_count_mock.assert_called_once()
    stripe_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type
    )
    increase_subscription_mock.assert_called_once_with(
        quantity=quantity
    )


@pytest.mark.parametrize('lease_level', LeaseLevel.NOT_TENANT_LEVELS)
def test__not_increment__ok(lease_level, mocker):

    # arrange
    account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        lease_level=lease_level,
        max_users=2
    )
    quantity = 4
    is_superuser = False
    auth_type = AuthTokenType.USER
    user = create_test_user(
        account=account,
        is_account_owner=True,
        email='master@test.test'
    )
    get_paid_users_count_mock = mocker.patch(
        'pneumatic_backend.accounts.models.Account.'
        'get_paid_users_count',
        return_value=4
    )
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    increase_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService.increase_subscription'
    )

    # act
    _increase_plan_users(
        account_id=account.id,
        is_superuser=is_superuser,
        auth_type=auth_type,
        increment=False
    )

    # assert
    get_paid_users_count_mock.assert_called_once()
    get_paid_users_count_mock.assert_called_once()
    stripe_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type
    )
    increase_subscription_mock.assert_called_once_with(
        quantity=quantity
    )


def test__tenant_increment__ok(mocker):

    # arrange
    master_account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        max_users=2
    )
    master_account_user = create_test_user(
        account=master_account,
        is_account_owner=True,
        email='master@test.test'
    )

    tenant_account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    create_test_user(
        account=tenant_account,
        is_account_owner=True,
        email='tenant@test.test'
    )

    quantity = 3
    is_superuser = False
    auth_type = AuthTokenType.USER

    get_paid_users_count_mock = mocker.patch(
        'pneumatic_backend.accounts.models.Account.'
        'get_paid_users_count',
        return_value=4
    )
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    increase_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService.increase_subscription'
    )

    # act
    _increase_plan_users(
        account_id=tenant_account.id,
        is_superuser=is_superuser,
        auth_type=auth_type
    )

    # assert
    get_paid_users_count_mock.assert_called_once()
    stripe_service_init_mock.assert_called_once_with(
        user=master_account_user,
        is_superuser=is_superuser,
        auth_type=auth_type
    )
    increase_subscription_mock.assert_called_once_with(
        quantity=quantity
    )


def test__tenant_not_increment__ok(mocker):

    # arrange
    master_account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        max_users=2
    )
    master_account_user = create_test_user(
        account=master_account,
        is_account_owner=True,
        email='master@test.test'
    )

    tenant_account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    create_test_user(
        account=tenant_account,
        is_account_owner=True,
        email='tenant@test.test'
    )

    quantity = 4
    is_superuser = False
    auth_type = AuthTokenType.USER

    get_paid_users_count_mock = mocker.patch(
        'pneumatic_backend.accounts.models.Account.'
        'get_paid_users_count',
        return_value=4
    )
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    increase_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService.increase_subscription'
    )

    # act
    _increase_plan_users(
        account_id=tenant_account.id,
        is_superuser=is_superuser,
        auth_type=auth_type,
        increment=False
    )

    # assert
    get_paid_users_count_mock.assert_called_once()
    stripe_service_init_mock.assert_called_once_with(
        user=master_account_user,
        is_superuser=is_superuser,
        auth_type=auth_type
    )
    increase_subscription_mock.assert_called_once_with(
        quantity=quantity
    )


def test__increment__quantity_not_changed__skip(mocker):

    # arrange
    is_superuser = True
    auth_type = AuthTokenType.API
    account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        max_users=1
    )
    create_test_user(
        account=account,
        is_account_owner=True,
        email='master@test.test'
    )
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    increase_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService.increase_subscription'
    )

    # act
    _increase_plan_users(
        account_id=account.id,
        is_superuser=is_superuser,
        auth_type=auth_type
    )

    # assert
    stripe_service_init_mock.assert_not_called()
    increase_subscription_mock.assert_not_called()


def test__increment__stripe_exception__not_increase(mocker):

    # arrange
    account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        max_users=2
    )
    quantity = 3
    is_superuser = False
    auth_type = AuthTokenType.USER

    user = create_test_user(
        account=account,
        is_account_owner=True,
        email='master@test.test'
    )
    get_paid_users_count_mock = mocker.patch(
        'pneumatic_backend.accounts.models.Account.'
        'get_paid_users_count',
        return_value=4
    )
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    message = 'message'
    increase_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService.increase_subscription',
        side_effect=StripeServiceException(message)
    )

    capture_sentry_message_mock = mocker.patch(
        'pneumatic_backend.payment.tasks.capture_sentry_message'
    )

    # act
    _increase_plan_users(
        account_id=account.id,
        is_superuser=is_superuser,
        auth_type=auth_type
    )

    # assert
    get_paid_users_count_mock.assert_called_once()
    stripe_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type
    )
    increase_subscription_mock.assert_called_once_with(
        quantity=quantity
    )
    assert capture_sentry_message_mock.call_count == 1


def test__increment__freemium__skip(mocker):

    # arrange
    is_superuser = False
    auth_type = AuthTokenType.USER

    account = create_test_account(
        plan=BillingPlanType.FREEMIUM,
        max_users=2
    )
    create_test_user(
        account=account,
        is_account_owner=True,
        email='master@test.test'
    )
    get_paid_users_count_mock = mocker.patch(
        'pneumatic_backend.accounts.models.Account.'
        'get_paid_users_count',
        return_value=4
    )

    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    increase_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService.increase_subscription'
    )

    # act
    _increase_plan_users(
        account_id=account.id,
        is_superuser=is_superuser,
        auth_type=auth_type
    )

    # assert
    get_paid_users_count_mock.assert_not_called()
    stripe_service_init_mock.assert_not_called()
    increase_subscription_mock.assert_not_called()


def test__increment__trial__skip(mocker):

    # arrange
    is_superuser = False
    auth_type = AuthTokenType.USER
    plan_expiration = timezone.now() + timedelta(days=30)
    account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        trial_ended=False,
        trial_start=timezone.now() - timedelta(minutes=1),
        plan_expiration=plan_expiration,
        trial_end=plan_expiration,
    )
    create_test_user(
        account=account,
        is_account_owner=True,
        email='master@test.test'
    )
    get_paid_users_count_mock = mocker.patch(
        'pneumatic_backend.accounts.models.Account.'
        'get_paid_users_count',
        return_value=4
    )

    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    increase_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService.increase_subscription'
    )

    # act
    _increase_plan_users(
        account_id=account.id,
        is_superuser=is_superuser,
        auth_type=auth_type
    )

    # assert
    get_paid_users_count_mock.assert_not_called()
    stripe_service_init_mock.assert_not_called()
    increase_subscription_mock.assert_not_called()


def test__increment__not_premium__skip(mocker):

    # arrange
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
    )

    is_superuser = False
    auth_type = AuthTokenType.USER

    get_paid_users_count_mock = mocker.patch(
        'pneumatic_backend.accounts.models.Account.'
        'get_paid_users_count'
    )
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    increase_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService.increase_subscription'
    )

    # act
    _increase_plan_users(
        account_id=account.id,
        is_superuser=is_superuser,
        auth_type=auth_type
    )

    # assert
    get_paid_users_count_mock.assert_not_called()
    stripe_service_init_mock.assert_not_called()
    increase_subscription_mock.assert_not_called()
