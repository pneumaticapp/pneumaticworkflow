import pytest
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from pneumatic_backend.accounts.services import AccountService
from pneumatic_backend.processes.tests.fixtures import (
    create_test_template,
    create_test_account,
    create_test_user,
)
from pneumatic_backend.payment.services.account import (
    AccountSubscriptionService
)
from pneumatic_backend.payment.entities import (
    SubscriptionDetails,
    BillingPeriod,
)
from pneumatic_backend.accounts.enums import (
    BillingPlanType,
)
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.accounts.enums import LeaseLevel
from pneumatic_backend.payment.services.exceptions import (
    DowngradeException
)
from pneumatic_backend.payment import messages


UserModel = get_user_model()
pytestmark = pytest.mark.django_db


def test_plan_changed__not_changes__ok():

    # arrange
    plan_expiration = timezone.now() + timedelta(days=30)
    period = BillingPeriod.MONTHLY
    account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        plan_expiration=plan_expiration,
        trial_start=timezone.now(),
        trial_end=plan_expiration,
        period=period,
    )
    user = create_test_user(account=account)
    is_superuser = True
    auth_type = AuthTokenType.WEBHOOK
    service = AccountSubscriptionService(
        instance=account,
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    details = SubscriptionDetails(
        quantity=account.accounts_count,
        max_users=account.max_users,
        billing_plan=account.billing_plan,
        plan_expiration=account.plan_expiration,
        trial_start=account.trial_start,
        trial_end=account.trial_end,
        billing_period=account.billing_period,
    )

    # act
    result = service._plan_changed(details)

    # assert
    assert result is False


def test_plan_changed__max_users_changed__ok():

    # arrange
    plan_expiration = timezone.now() + timedelta(days=30)
    period = BillingPeriod.MONTHLY
    account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        plan_expiration=plan_expiration,
        period=period,
    )
    user = create_test_user(account=account)
    is_superuser = True
    auth_type = AuthTokenType.WEBHOOK
    service = AccountSubscriptionService(
        instance=account,
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    details = SubscriptionDetails(
        quantity=account.accounts_count,
        max_users=account.max_users + 1,
        billing_plan=account.billing_plan,
        plan_expiration=account.plan_expiration,
        trial_start=account.trial_start,
        trial_end=account.trial_end,
        billing_period=account.billing_period,
    )

    # act
    result = service._plan_changed(details)

    # assert
    assert result is True


def test_plan_changed__plan_expiration_changed__ok():

    # arrange
    plan_expiration = timezone.now() + timedelta(days=30)
    period = BillingPeriod.MONTHLY
    account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        plan_expiration=plan_expiration,
        period=period,
    )
    user = create_test_user(account=account)
    is_superuser = True
    auth_type = AuthTokenType.WEBHOOK
    service = AccountSubscriptionService(
        instance=account,
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    details = SubscriptionDetails(
        quantity=account.accounts_count,
        max_users=account.max_users,
        billing_plan=account.billing_plan,
        plan_expiration=account.plan_expiration + timedelta(days=30),
        trial_start=account.trial_start,
        trial_end=account.trial_end,
        billing_period=account.billing_period,
    )

    # act
    result = service._plan_changed(details)

    # assert
    assert result is True


def test_plan_changed__plan_changed__ok():

    # arrange
    period = None
    account = create_test_account(
        plan=BillingPlanType.FREEMIUM,
        period=period,
    )
    user = create_test_user(account=account)
    is_superuser = True
    auth_type = AuthTokenType.WEBHOOK
    service = AccountSubscriptionService(
        instance=account,
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    details = SubscriptionDetails(
        quantity=account.accounts_count,
        max_users=account.max_users,
        billing_plan=BillingPlanType.FRACTIONALCOO,
        plan_expiration=account.plan_expiration,
        trial_start=account.trial_start,
        trial_end=account.trial_end,
        billing_period=account.billing_period,
    )

    # act
    result = service._plan_changed(details)

    # assert
    assert result is True


def test_plan_changed__first_trial__ok():

    # arrange
    trial_start = timezone.now() - timedelta(minutes=1)
    trial_end = timezone.now() + timedelta(days=30)
    plan_expiration = trial_end
    period = None

    account = create_test_account(
        plan=BillingPlanType.FREEMIUM,
        period=period
    )
    user = create_test_user(account=account)
    is_superuser = True
    auth_type = AuthTokenType.WEBHOOK
    service = AccountSubscriptionService(
        instance=account,
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )
    details = SubscriptionDetails(
        quantity=account.accounts_count,
        max_users=account.max_users,
        billing_plan=BillingPlanType.PREMIUM,
        plan_expiration=plan_expiration,
        trial_start=trial_start,
        trial_end=trial_end,
        billing_period=account.billing_period,
    )

    # act
    result = service._plan_changed(details)

    # assert
    assert result is True


def test_plan_changed__billing_period__ok():

    # arrange
    plan_expiration = timezone.now() + timedelta(days=30)
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
        plan_expiration=plan_expiration,
        trial_start=timezone.now(),
        trial_end=plan_expiration,
        period=BillingPeriod.MONTHLY,
    )
    user = create_test_user(account=account)
    is_superuser = True
    auth_type = AuthTokenType.WEBHOOK
    service = AccountSubscriptionService(
        instance=account,
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )
    details = SubscriptionDetails(
        quantity=account.accounts_count,
        max_users=account.max_users,
        billing_plan=account.billing_plan,
        plan_expiration=account.plan_expiration,
        trial_start=account.trial_start,
        trial_end=account.trial_end,
        billing_period=BillingPeriod.YEARLY,
    )

    # act
    result = service._plan_changed(details)

    # assert
    assert result is True


def test_plan_changed__quantity__ok():

    # arrange
    plan_expiration = timezone.now() + timedelta(days=30)
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
        plan_expiration=plan_expiration,
        trial_start=timezone.now(),
        trial_end=plan_expiration,
        period=BillingPeriod.MONTHLY,
    )
    create_test_account(master_account=account, lease_level=LeaseLevel.TENANT)
    create_test_account(master_account=account, lease_level=LeaseLevel.TENANT)
    user = create_test_user(account=account)
    is_superuser = True
    auth_type = AuthTokenType.WEBHOOK
    service = AccountSubscriptionService(
        instance=account,
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )
    details = SubscriptionDetails(
        quantity=1,
        max_users=account.max_users,
        billing_plan=account.billing_plan,
        plan_expiration=account.plan_expiration,
        trial_start=account.trial_start,
        trial_end=account.trial_end,
        billing_period=account.billing_period,
    )

    # act
    result = service._plan_changed(details)

    # assert
    assert result is True


def test_create__freemium_to_trial__ok(mocker, identify_mock):

    # arrange
    account = create_test_account(
        plan=BillingPlanType.FREEMIUM,
        trial_ended=False
    )
    user = create_test_user(account=account)
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    account_service_partial_update_mock = mocker.patch(
        'pneumatic_backend.accounts.services.'
        'AccountService.partial_update'
    )
    analytics_trial_subscription_created_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'trial_subscription_created'
    )
    analytics_subscription_created_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'subscription_created'
    )
    payment_card_provided = True
    trial_start = timezone.now() - timedelta(minutes=1)
    plan_expiration = timezone.now() + timedelta(days=30)
    details = SubscriptionDetails(
        quantity=account.accounts_count,
        max_users=10,
        billing_plan=BillingPlanType.PREMIUM,
        billing_period=BillingPeriod.YEARLY,
        plan_expiration=plan_expiration,
        trial_start=trial_start,
        trial_end=plan_expiration
    )
    is_superuser = True
    auth_type = AuthTokenType.WEBHOOK
    service = AccountSubscriptionService(
        instance=account,
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # act
    service._create(
        details=details,
        payment_card_provided=payment_card_provided
    )

    # assert
    account_service_init_mock.assert_called_once_with(
        instance=account,
        user=user,
        auth_type=auth_type,
        is_superuser=is_superuser,
    )
    account_service_partial_update_mock.assert_called_once_with(
        billing_plan=details.billing_plan,
        billing_period=details.billing_period,
        plan_expiration=plan_expiration,
        max_users=details.max_users,
        payment_card_provided=payment_card_provided,
        trial_start=trial_start,
        trial_end=plan_expiration,
        tmp_subscription=False,
        force_save=True
    )
    analytics_subscription_created_mock.assert_called_once_with(user)
    analytics_trial_subscription_created_mock.assert_called_once_with(user)
    identify_mock.assert_called_once_with(user)


def test_create__trial_ended__not_trial(mocker, identify_mock):

    # arrange
    account = create_test_account(
        plan=BillingPlanType.FREEMIUM,
        trial_ended=True
    )
    user = create_test_user(account=account)
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    account_service_partial_update_mock = mocker.patch(
        'pneumatic_backend.accounts.services.'
        'AccountService.partial_update'
    )
    analytics_trial_subscription_created_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'trial_subscription_created'
    )
    analytics_subscription_created_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'subscription_created'
    )
    payment_card_provided = True
    trial_start = timezone.now() - timedelta(minutes=1)
    plan_expiration = timezone.now() + timedelta(days=30)
    details = SubscriptionDetails(
        quantity=account.accounts_count,
        max_users=10,
        billing_plan=BillingPlanType.PREMIUM,
        billing_period=BillingPeriod.MONTHLY,
        plan_expiration=plan_expiration,
        trial_start=trial_start,
        trial_end=plan_expiration
    )
    is_superuser = True
    auth_type = AuthTokenType.WEBHOOK
    service = AccountSubscriptionService(
        instance=account,
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # act
    service._create(
        details=details,
        payment_card_provided=payment_card_provided
    )

    # assert
    account_service_init_mock.assert_called_once_with(
        instance=account,
        user=user,
        auth_type=auth_type,
        is_superuser=is_superuser,
    )
    account_service_partial_update_mock.assert_called_once_with(
        billing_plan=details.billing_plan,
        billing_period=details.billing_period,
        plan_expiration=plan_expiration,
        max_users=details.max_users,
        payment_card_provided=payment_card_provided,
        tmp_subscription=False,
        force_save=True
    )
    analytics_subscription_created_mock.assert_called_once_with(user)
    analytics_trial_subscription_created_mock.assert_not_called()
    identify_mock.assert_called_once_with(user)


def test_create__freemium_to_premium__ok(mocker, identify_mock):

    # arrange
    account = create_test_account(
        plan=BillingPlanType.FREEMIUM,
        payment_card_provided=False
    )
    user = create_test_user(account=account)
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    account_service_partial_update_mock = mocker.patch(
        'pneumatic_backend.accounts.services.'
        'AccountService.partial_update'
    )
    analytics_subscription_created_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'subscription_created'
    )
    analytics_trial_subscription_created_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'trial_subscription_created'
    )
    payment_card_provided = True
    plan_expiration = timezone.now() + timedelta(days=30)
    details = SubscriptionDetails(
        quantity=account.accounts_count,
        max_users=10,
        billing_plan=BillingPlanType.UNLIMITED,
        billing_period=BillingPeriod.MONTHLY,
        plan_expiration=plan_expiration,
        trial_start=None,
        trial_end=None
    )
    is_superuser = True
    auth_type = AuthTokenType.WEBHOOK
    service = AccountSubscriptionService(
        instance=account,
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # act
    service._create(
        details=details,
        payment_card_provided=payment_card_provided
    )

    # assert
    account_service_init_mock.assert_called_once_with(
        instance=account,
        user=user,
        auth_type=auth_type,
        is_superuser=is_superuser,
    )
    account_service_partial_update_mock.assert_called_once_with(
        billing_plan=details.billing_plan,
        billing_period=details.billing_period,
        plan_expiration=plan_expiration,
        max_users=details.max_users,
        payment_card_provided=payment_card_provided,
        trial_start=None,
        trial_end=None,
        tmp_subscription=False,
        force_save=True
    )
    analytics_subscription_created_mock.assert_called_once_with(user)
    analytics_trial_subscription_created_mock.assert_not_called()
    identify_mock.assert_called_once_with(user)


def test_create__tmp_subscription_to_premium_trial__ok(mocker, identify_mock):

    # arrange
    account = create_test_account(
        max_users=10,
        plan=BillingPlanType.PREMIUM,
        plan_expiration=timezone.now() + timedelta(hours=1),
        payment_card_provided=True,
        tmp_subscription=True
    )
    user = create_test_user(account=account)
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    account_service_partial_update_mock = mocker.patch(
        'pneumatic_backend.accounts.services.'
        'AccountService.partial_update'
    )
    analytics_subscription_created_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'subscription_created'
    )
    analytics_trial_subscription_created_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'trial_subscription_created'
    )
    payment_card_provided = True
    trial_start = timezone.now()
    plan_expiration = timezone.now() + timedelta(days=7)
    details = SubscriptionDetails(
        quantity=account.accounts_count,
        max_users=10,
        billing_plan=BillingPlanType.UNLIMITED,
        billing_period=BillingPeriod.YEARLY,
        plan_expiration=plan_expiration,
        trial_start=trial_start,
        trial_end=plan_expiration,
    )
    is_superuser = True
    auth_type = AuthTokenType.WEBHOOK
    service = AccountSubscriptionService(
        instance=account,
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # act
    service._create(
        details=details,
        payment_card_provided=payment_card_provided
    )

    # assert
    account_service_init_mock.assert_called_once_with(
        instance=account,
        user=user,
        auth_type=auth_type,
        is_superuser=is_superuser,
    )
    account_service_partial_update_mock.assert_called_once_with(
        billing_plan=details.billing_plan,
        billing_period=details.billing_period,
        plan_expiration=plan_expiration,
        max_users=details.max_users,
        payment_card_provided=payment_card_provided,
        trial_start=trial_start,
        trial_end=plan_expiration,
        tmp_subscription=False,
        force_save=True
    )
    analytics_subscription_created_mock.assert_called_once_with(user)
    analytics_trial_subscription_created_mock.assert_called_once_with(user)
    identify_mock.assert_called_once_with(user)


def test_public_create__plan_changed__ok(mocker, identify_mock):

    # arrange
    payment_card_provided = True
    account = create_test_account()
    user = create_test_user(account=account)

    plan_changed = True
    plan_changed_mock = mocker.patch(
        'pneumatic_backend.payment.services.account.'
        'AccountSubscriptionService._plan_changed',
        return_value=plan_changed
    )
    private_create_mock = mocker.patch(
        'pneumatic_backend.payment.services.account.'
        'AccountSubscriptionService._create',
    )
    is_superuser = True
    auth_type = AuthTokenType.WEBHOOK
    service = AccountSubscriptionService(
        instance=account,
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )
    details_mock = mocker.Mock()

    # act
    service.create(
        details=details_mock,
        payment_card_provided=payment_card_provided,
    )

    # assert
    plan_changed_mock.assert_called_once_with(details_mock)
    private_create_mock.assert_called_once_with(
        details=details_mock,
        payment_card_provided=payment_card_provided,
    )


def test_public_create__plan_not_changed__skip(mocker, identify_mock):

    # arrange
    payment_card_provided = True
    account = create_test_account()
    user = create_test_user(account=account)

    plan_changed = False
    plan_changed_mock = mocker.patch(
        'pneumatic_backend.payment.services.account.'
        'AccountSubscriptionService._plan_changed',
        return_value=plan_changed
    )
    private_create_mock = mocker.patch(
        'pneumatic_backend.payment.services.account.'
        'AccountSubscriptionService._create'
    )
    is_superuser = True
    auth_type = AuthTokenType.WEBHOOK
    service = AccountSubscriptionService(
        instance=account,
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )
    details_mock = mocker.Mock()

    # act
    service.create(
        details=details_mock,
        payment_card_provided=payment_card_provided,
    )

    # assert
    plan_changed_mock.assert_called_once_with(details_mock)
    private_create_mock.assert_not_called()


def test_update__trial_to_premium__ok(mocker, identify_mock):

    # arrange
    trial_start = timezone.now() - timedelta(minutes=1)
    plan_expiration = timezone.now() + timedelta(days=1)
    account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        plan_expiration=plan_expiration,
        trial_start=trial_start,
        trial_end=plan_expiration,
        trial_ended=False
    )
    user = create_test_user(account=account)
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    account_service_partial_update_mock = mocker.patch(
        'pneumatic_backend.accounts.services.'
        'AccountService.partial_update'
    )
    analytics_subscription_converted_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'subscription_converted'
    )
    is_superuser = True
    auth_type = AuthTokenType.WEBHOOK
    service = AccountSubscriptionService(
        instance=account,
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )
    details = SubscriptionDetails(
        quantity=account.accounts_count,
        max_users=10,
        billing_plan=BillingPlanType.PREMIUM,
        billing_period=BillingPeriod.MONTHLY,
        plan_expiration=plan_expiration,
        trial_start=trial_start,
        trial_end=plan_expiration
    )

    # act
    service._update(details)

    # assert
    account_service_init_mock.assert_called_once_with(
        instance=account,
        user=user,
        auth_type=auth_type,
        is_superuser=is_superuser,
    )
    account_service_partial_update_mock.assert_called_once_with(
        billing_plan=details.billing_plan,
        billing_period=BillingPeriod.MONTHLY,
        plan_expiration=details.plan_expiration,
        max_users=details.max_users,
        payment_card_provided=True,
        trial_ended=True,
        tmp_subscription=False,
        force_save=True
    )
    analytics_subscription_converted_mock.assert_called_once_with(user)
    identify_mock.assert_called_once_with(user)


def test_update__premium_to_premium__ok(mocker, identify_mock):

    # arrange
    account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        plan_expiration=timezone.now() + timedelta(days=1),
        trial_end=timezone.now() - timedelta(days=1)
    )
    user = create_test_user(account=account)
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    account_service_partial_update_mock = mocker.patch(
        'pneumatic_backend.accounts.services.'
        'AccountService.partial_update'
    )
    analytics_subscription_updated_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'subscription_updated'
    )
    is_superuser = True
    auth_type = AuthTokenType.WEBHOOK
    service = AccountSubscriptionService(
        instance=account,
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )
    new_plan_expiration = timezone.now() + timedelta(days=30)
    details = SubscriptionDetails(
        quantity=account.accounts_count,
        max_users=10,
        billing_plan=BillingPlanType.UNLIMITED,
        billing_period=BillingPeriod.MONTHLY,
        plan_expiration=new_plan_expiration,
        trial_start=None,
        trial_end=None
    )

    # act
    service._update(details)

    # assert
    account_service_init_mock.assert_called_once_with(
        instance=account,
        user=user,
        auth_type=auth_type,
        is_superuser=is_superuser,
    )
    account_service_partial_update_mock.assert_called_once_with(
        billing_plan=details.billing_plan,
        billing_period=details.billing_period,
        plan_expiration=details.plan_expiration,
        max_users=details.max_users,
        payment_card_provided=True,
        tmp_subscription=False,
        trial_ended=True,
        force_save=True
    )
    analytics_subscription_updated_mock.assert_called_once_with(user)
    identify_mock.assert_called_once_with(user)


def test_public_update__plan_changed__ok(mocker):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)

    plan_changed = True
    plan_changed_mock = mocker.patch(
        'pneumatic_backend.payment.services.account.'
        'AccountSubscriptionService._plan_changed',
        return_value=plan_changed
    )
    private_update_mock = mocker.patch(
        'pneumatic_backend.payment.services.account.'
        'AccountSubscriptionService._update',
    )
    is_superuser = True
    auth_type = AuthTokenType.WEBHOOK
    service = AccountSubscriptionService(
        instance=account,
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )
    details_mock = mocker.Mock()

    # act
    service.update(
        details=details_mock,
    )

    # assert
    plan_changed_mock.assert_called_once_with(details_mock)
    private_update_mock.assert_called_once_with(details=details_mock)


def test_public_update__plan_not_changed__skip(mocker):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)

    plan_changed = False
    plan_changed_mock = mocker.patch(
        'pneumatic_backend.payment.services.account.'
        'AccountSubscriptionService._plan_changed',
        return_value=plan_changed
    )
    private_update_mock = mocker.patch(
        'pneumatic_backend.payment.services.account.'
        'AccountSubscriptionService._update',
    )
    is_superuser = True
    auth_type = AuthTokenType.WEBHOOK
    service = AccountSubscriptionService(
        instance=account,
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )
    details_mock = mocker.Mock()

    # act
    service.update(
        details=details_mock,
    )

    # assert
    plan_changed_mock.assert_called_once_with(details_mock)
    private_update_mock.assert_not_called()


def test_expired__ok(mocker):

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(account=account)
    period_end_date = timezone.now() + timedelta(days=30)

    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    account_service_partial_update_mock = mocker.patch(
        'pneumatic_backend.accounts.services.'
        'AccountService.partial_update'
    )
    is_superuser = True
    auth_type = AuthTokenType.WEBHOOK
    service = AccountSubscriptionService(
        instance=account,
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # act
    service.expired(period_end_date)

    # arrange
    account_service_init_mock.assert_called_once_with(
        instance=account,
        user=user,
        auth_type=auth_type,
        is_superuser=is_superuser,
    )
    account_service_partial_update_mock.assert_called_once_with(
        plan_expiration=period_end_date,
        trial_ended=True,
        force_save=True
    )


def test_cancel__ok(mocker):

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(account=account)
    analytics_subscription_canceled_created_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'subscription_canceled'
    )
    expired_mock = mocker.patch(
        'pneumatic_backend.payment.services.account.'
        'AccountSubscriptionService.expired'
    )
    is_superuser = True
    auth_type = AuthTokenType.WEBHOOK
    service = AccountSubscriptionService(
        instance=account,
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )
    plan_expiration = timezone.now() + timedelta(days=1)

    # act
    service.cancel(plan_expiration)

    # arrange
    expired_mock.assert_called_once_with(plan_expiration)
    analytics_subscription_canceled_created_mock.assert_called_once_with(user)


def test_downgrade_to_free__freemium__skip(mocker):

    # arrange
    account = create_test_account(plan=BillingPlanType.FREEMIUM)
    user = create_test_user(account=account)
    analytics_subscription_canceled_created_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'subscription_canceled'
    )
    is_superuser = True
    auth_type = AuthTokenType.WEBHOOK
    service = AccountSubscriptionService(
        instance=account,
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # act
    service.downgrade_to_free()

    # assert
    analytics_subscription_canceled_created_mock.assert_not_called()


@pytest.mark.parametrize('plan', BillingPlanType.PAYMENT_PLANS)
def test_downgrade_to_free__expired_premium__ok(plan, mocker):

    # arrange
    plan_expiration = timezone.now() - timedelta(days=1)
    account = create_test_account(
        plan=plan,
        plan_expiration=plan_expiration,
    )
    user = create_test_user(account=account)
    template = create_test_template(
        is_public=True,
        is_active=True,
        user=user
    )
    account.active_templates = 2
    account.max_active_templates = 3
    account.save(update_fields=['active_templates', 'max_active_templates'])
    analytics_subscription_canceled_created_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'subscription_canceled'
    )
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    account_service_partial_update_mock = mocker.patch(
        'pneumatic_backend.accounts.services.'
        'AccountService.partial_update'
    )

    is_superuser = True
    auth_type = AuthTokenType.WEBHOOK
    service = AccountSubscriptionService(
        instance=account,
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # act
    service.downgrade_to_free()

    # assert
    account_service_init_mock.assert_called_once_with(
        instance=account,
        user=user,
        auth_type=auth_type,
        is_superuser=is_superuser,
    )
    account_service_partial_update_mock.assert_called_once_with(
        billing_plan=BillingPlanType.FREEMIUM,
        billing_period=None,
        plan_expiration=None,
        active_templates=1,
        max_users=settings.FREEMIUM_MAX_USERS,
        trial_ended=True,
        force_save=True
    )
    template.refresh_from_db()
    assert template.is_active is False
    analytics_subscription_canceled_created_mock.assert_called_once_with(user)


@pytest.mark.parametrize('plan', BillingPlanType.PAYMENT_PLANS)
def test_downgrade_to_free__not_expired_premium__ok(plan, mocker):

    # arrange
    plan_expiration = timezone.now() + timedelta(days=1)
    account = create_test_account(
        plan=plan,
        plan_expiration=plan_expiration,
    )
    user = create_test_user(account=account)
    template = create_test_template(
        is_public=True,
        is_active=True,
        user=user
    )
    analytics_subscription_canceled_created_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'subscription_canceled'
    )
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    account_service_partial_update_mock = mocker.patch(
        'pneumatic_backend.accounts.services.'
        'AccountService.partial_update'
    )
    is_superuser = True
    auth_type = AuthTokenType.WEBHOOK
    service = AccountSubscriptionService(
        instance=account,
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # act
    with pytest.raises(DowngradeException) as ex:
        service.downgrade_to_free()

    # assert
    assert ex.value.message == messages.MSG_BL_0022
    account_service_init_mock.assert_not_called()
    account_service_partial_update_mock.assert_not_called()
    template.refresh_from_db()
    assert template.is_active is True
    analytics_subscription_canceled_created_mock.assert_not_called()


def test_downgrade_to_free__active_templates_reached__ok(mocker):

    # arrange
    plan_expiration = timezone.now() - timedelta(days=1)
    account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        plan_expiration=plan_expiration,
    )
    user = create_test_user(account=account)
    template = create_test_template(
        is_public=True,
        is_active=True,
        user=user
    )
    account.active_templates = 4
    account.max_active_templates = 3
    account.save(update_fields=['active_templates', 'max_active_templates'])

    analytics_subscription_canceled_created_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'subscription_canceled'
    )
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    account_service_partial_update_mock = mocker.patch(
        'pneumatic_backend.accounts.services.'
        'AccountService.partial_update'
    )
    is_superuser = True
    auth_type = AuthTokenType.WEBHOOK
    service = AccountSubscriptionService(
        instance=account,
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # act
    service.downgrade_to_free()

    # assert
    account_service_init_mock.assert_called_once_with(
        instance=account,
        user=user,
        auth_type=auth_type,
        is_superuser=is_superuser,
    )
    account_service_partial_update_mock.assert_called_once_with(
        billing_plan=BillingPlanType.FREEMIUM,
        billing_period=None,
        plan_expiration=None,
        active_templates=0,
        max_users=settings.FREEMIUM_MAX_USERS,
        trial_ended=True,
        force_save=True
    )
    template.refresh_from_db()
    assert template.is_active is False
    analytics_subscription_canceled_created_mock.assert_called_once_with(user)


def test_downgrade_to_free__master__ok(mocker):

    # arrange
    plan_expiration = timezone.now() - timedelta(days=1)
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
        plan_expiration=plan_expiration,
    )
    user = create_test_user(account=account)
    mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'subscription_canceled'
    )
    mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    mocker.patch(
        'pneumatic_backend.accounts.services.'
        'AccountService.partial_update'
    )
    is_superuser = True
    auth_type = AuthTokenType.WEBHOOK
    service = AccountSubscriptionService(
        instance=account,
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # act
    service.downgrade_to_free()

    # assert


def test_payment_card_provided__ok(mocker, identify_mock):

    # arrange
    account = create_test_account(payment_card_provided=False)
    user = create_test_user(account=account)
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    account_service_partial_update_mock = mocker.patch(
        'pneumatic_backend.accounts.services.'
        'AccountService.partial_update'
    )
    is_superuser = True
    auth_type = AuthTokenType.WEBHOOK
    service = AccountSubscriptionService(
        instance=account,
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # act
    service.payment_card_provided(value=True)

    # assert
    account_service_init_mock.assert_called_once_with(
        instance=account,
        user=user,
        auth_type=auth_type,
        is_superuser=is_superuser,
    )
    account_service_partial_update_mock.assert_called_once_with(
        payment_card_provided=True,
        force_save=True
    )
    identify_mock.assert_called_once_with(user)
