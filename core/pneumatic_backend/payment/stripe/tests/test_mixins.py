import pytest
import stripe
from django.utils import timezone
from datetime import timedelta
from pneumatic_backend.accounts.enums import (
    LeaseLevel,
    BillingPlanType,
)
from pneumatic_backend.payment.stripe.exceptions import (
    NotFoundAccountForSubscription
)
from pneumatic_backend.payment.stripe.mixins import StripeMixin
from pneumatic_backend.processes.tests.fixtures import (
    create_test_account,
)
from pneumatic_backend.payment.models import Price
from pneumatic_backend.payment.enums import (
    BillingPeriod,
    PriceStatus,
    PriceType,
)
from pneumatic_backend.payment.tests.fixtures import (
    create_test_recurring_price,
    create_test_product,
)
from pneumatic_backend.payment import messages


pytestmark = pytest.mark.django_db


def test_get_customer__ok(mocker):

    # arrange
    customer_stripe_id = "cus_Nx9XuHa4xteob3"
    customer_mock = mocker.Mock()
    customer_retrieve_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.mixins.'
        'stripe.Customer.retrieve',
        return_value=customer_mock
    )
    service = StripeMixin()

    # act
    result = service._get_customer(customer_stripe_id)

    # assert
    customer_retrieve_mock.assert_called_once_with(id=customer_stripe_id)
    assert result == customer_mock


def test_get_customer__not_existent_stripe_id__return_none(mocker):

    # arrange
    customer_stripe_id = "cus_123"
    customer_retrieve_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.mixins.'
        'stripe.Customer.retrieve',
        side_effect=stripe.error.InvalidRequestError(
            param='id',
            message='not found'
        )
    )
    service = StripeMixin()

    # act
    result = service._get_customer(customer_stripe_id)

    # assert
    customer_retrieve_mock.assert_called_once_with(id=customer_stripe_id)
    assert result is None


def test_get_customer_by_email__ok(mocker):

    # arrange
    email = 'owner@test.test'
    customer_mock = mocker.Mock()
    result_mock = {'data': [customer_mock]}
    customer_search_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.mixins.'
        'stripe.Customer.search',
        return_value=result_mock
    )
    service = StripeMixin()

    # act
    result = service._get_customer_by_email(email)

    # assert
    customer_search_mock.assert_called_once_with(query=f"email:'{email}'")
    assert result == customer_mock


def test_get_customer_by_email__multiple_result__return_first(mocker):

    # arrange
    email = 'owner@test.test'
    customer_mock = mocker.Mock()
    result_mock = {'data': [customer_mock, mocker.Mock(123)]}
    customer_search_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.mixins.'
        'stripe.Customer.search',
        return_value=result_mock
    )
    service = StripeMixin()

    # act
    result = service._get_customer_by_email(email)

    # assert
    customer_search_mock.assert_called_once_with(query=f"email:'{email}'")
    assert result == customer_mock


def test_get_customer_by_email__not_found__return_none(mocker):

    # arrange
    email = 'owner@test.test'
    result_mock = {'data': []}
    customer_search_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.mixins.'
        'stripe.Customer.search',
        return_value=result_mock
    )
    service = StripeMixin()

    # act
    result = service._get_customer_by_email(email)

    # assert
    customer_search_mock.assert_called_once_with(query=f"email:'{email}'")
    assert result is None


def test_get_subscription_by_id__ok(mocker):

    # arrange
    subscription_stripe_id = "sub_Nx9XuHa4xteob3"
    subscription_mock = mocker.Mock()
    customer_retrieve_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.mixins.'
        'stripe.Subscription.retrieve',
        return_value=subscription_mock
    )
    service = StripeMixin()

    # act
    result = service._get_subscription_by_id(
        stripe_id=subscription_stripe_id
    )

    # assert
    customer_retrieve_mock.assert_called_once_with(id=subscription_stripe_id)
    assert result == subscription_mock


def test_get_payment_method__ok(mocker):

    # arrange
    method_stripe_id = "pm_Nx9XuHa4xteob3"
    method_mock = mocker.Mock()
    method_retrieve_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.mixins.'
        'stripe.PaymentMethod.retrieve',
        return_value=method_mock
    )
    service = StripeMixin()

    # act
    result = service._get_payment_method(method_stripe_id)

    # assert
    method_retrieve_mock.assert_called_once_with(id=method_stripe_id)
    assert result == method_mock


@pytest.mark.parametrize('lease_level', LeaseLevel.NOT_TENANT_LEVELS)
def test_get_account__ok(lease_level):

    # arrange
    customer_stripe_id = "cus_Nx9XuHa4xteob3"
    create_test_account(
        stripe_id=customer_stripe_id,
        lease_level=LeaseLevel.TENANT
    )
    account = create_test_account(
        stripe_id=customer_stripe_id,
        lease_level=lease_level
    )

    service = StripeMixin()

    # act
    result = service._get_account(customer_stripe_id)

    # assert
    assert result == account


def test__get_account__not_found__return_none():

    # arrange
    customer_stripe_id = "cus_Nx9XuHa4xteob3"
    create_test_account(
        stripe_id=customer_stripe_id,
        lease_level=LeaseLevel.TENANT
    )
    service = StripeMixin()

    # act
    result = service._get_account(customer_stripe_id)

    # assert
    assert result is None


@pytest.mark.parametrize('status', ('active', 'trialing', 'past_due'))
def test_get_subscription_for_account__main_subs_empty_metadata__ok(
    status,
    mocker
):

    # arrange
    account = create_test_account(lease_level=LeaseLevel.STANDARD)
    customer = mocker.Mock()
    main_subscription_mock = mocker.Mock(metadata={}, status=status)
    tenant_1_subscription_mock = mocker.Mock()
    tenant_2_subscription_mock = mocker.Mock()
    subscriptions_mock = [
        tenant_1_subscription_mock,
        main_subscription_mock,
        tenant_2_subscription_mock,
    ]
    subscription_list_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.mixins.'
        'stripe.Subscription.list',
        return_value=subscriptions_mock
    )
    service = StripeMixin()

    # act
    result = service._get_subscription_for_account(
        customer=customer,
        subscription_account=account
    )

    # assert
    subscription_list_mock.assert_called_once_with(customer=customer)
    assert result == main_subscription_mock


def test_get_subscription_for_account__main_subscription__ok(
    mocker
):

    # arrange
    account = create_test_account(lease_level=LeaseLevel.STANDARD)
    customer = mocker.Mock()
    main_subscription_mock = mocker.Mock(
        metadata={'account_id': str(account.id)},
        status='trialing'
    )
    tenant_1_subscription_mock = mocker.Mock()
    tenant_2_subscription_mock = mocker.Mock()
    subscription_list_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.mixins.'
        'stripe.Subscription.list',
        return_value=[
            tenant_1_subscription_mock,
            main_subscription_mock,
            tenant_2_subscription_mock,
        ]
    )
    service = StripeMixin()

    # act
    result = service._get_subscription_for_account(
        customer=customer,
        subscription_account=account
    )

    # assert
    subscription_list_mock.assert_called_once_with(customer=customer)
    assert result == main_subscription_mock


@pytest.mark.parametrize('status', ('active', 'trialing', 'past_due'))
def test_get_subscription_for_account__tenant__ok(
    status,
    mocker
):

    # arrange
    master_account = create_test_account(lease_level=LeaseLevel.STANDARD)
    tenant_1 = create_test_account(
        master_account=master_account,
        lease_level=LeaseLevel.TENANT,
        tenant_name='Tenant 1'
    )
    tenant_2 = create_test_account(
        master_account=master_account,
        lease_level=LeaseLevel.TENANT,
        tenant_name='Tenant 2'
    )
    customer = mocker.Mock()
    main_subscription_mock = mocker.Mock(metadata={}, status=status)
    tenant_1_subscription_mock = mocker.Mock(
        metadata={'account_id': str(tenant_1.id)},
        status=status
    )
    tenant_2_subscription_mock = mocker.Mock(
        metadata={'account_id': str(tenant_2.id)},
        status=status
    )
    subscription_list_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.mixins.'
        'stripe.Subscription.list',
        return_value=[
            main_subscription_mock,
            tenant_1_subscription_mock,
            tenant_2_subscription_mock,
        ]
    )
    service = StripeMixin()

    # act
    result = service._get_subscription_for_account(
        customer=customer,
        subscription_account=tenant_2
    )

    # assert
    subscription_list_mock.assert_called_once_with(customer=customer)
    assert result == tenant_2_subscription_mock


def test_get_subscription_for_account__tenant_invalid_metadata__skip(
    mocker
):

    # arrange
    master_account = create_test_account(lease_level=LeaseLevel.STANDARD)
    tenant = create_test_account(
        master_account=master_account,
        lease_level=LeaseLevel.TENANT,
        tenant_name='Tenant'
    )
    customer = mocker.Mock()
    tenant_subscription_mock = mocker.Mock(
        metadata={'account_id': f'{tenant.id}a'},
        status='active'
    )
    subscription_list_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.mixins.'
        'stripe.Subscription.list',
        return_value=[
            tenant_subscription_mock,
        ]
    )
    capture_sentry_message_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.mixins.capture_sentry_message'
    )
    service = StripeMixin()

    # act
    result = service._get_subscription_for_account(
        customer=customer,
        subscription_account=tenant
    )

    # assert
    subscription_list_mock.assert_called_once_with(customer=customer)
    capture_sentry_message_mock.assert_called_once()
    assert result is None


def test_get_subscription_for_account__not_found__return_none(mocker):

    # arrange
    master_account = create_test_account(lease_level=LeaseLevel.STANDARD)
    customer = mocker.Mock()
    subscription_list_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.mixins.'
        'stripe.Subscription.list',
        return_value=[]
    )
    service = StripeMixin()

    # act
    result = service._get_subscription_for_account(
        customer=customer,
        subscription_account=master_account
    )

    # assert
    subscription_list_mock.assert_called_once_with(customer=customer)
    assert result is None


def test_get_aware_datetime_from_timestamp__ok():

    # arrange
    timestamp = 1688065072
    service = StripeMixin()

    # act
    result = service._get_aware_datetime_from_timestamp(timestamp)

    # assert
    str_result = result.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    assert str_result == '2023-06-29T18:57:52.000000Z'


def test_get_aware_datetime_from_timestamp__not_value__return_none():

    # arrange
    timestamp = None
    service = StripeMixin()

    # act
    result = service._get_aware_datetime_from_timestamp(timestamp)

    # assert
    assert result is None


def test_get_subscription_details__premium_trial__ok(mocker):

    # arrange
    trial_end = timezone.now() + timedelta(days=7)
    trial_end_timestamp = trial_end.timestamp()
    trial_start = timezone.now()
    trial_start_timestamp = trial_start.timestamp()
    period_end_date = timezone.now() + timedelta(days=15)
    period_end_date_timestamp = period_end_date.timestamp()
    price_stripe_id = 'price_123'
    product_code = 'premium'
    billing_period = BillingPeriod.YEARLY
    product = create_test_product(code=product_code)
    create_test_recurring_price(
        stripe_id=price_stripe_id,
        product=product,
        period=billing_period
    )
    quantity = 10
    price_mock = mocker.Mock(id=price_stripe_id)
    item_mock = mocker.MagicMock(price=price_mock)
    create_price_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.mixins.'
        'StripeMixin._create_price'
    )
    subscription = {
        'current_period_end': period_end_date_timestamp,
        'quantity': quantity,
        'items': mocker.Mock(data=[item_mock]),
        'trial_start': trial_start_timestamp,
        'trial_end': trial_end_timestamp,
    }
    service = StripeMixin()

    # act
    result = service.get_subscription_details(subscription)

    # assert
    create_price_mock.assert_not_called()
    assert result.max_users == quantity
    assert result.quantity == quantity
    assert result.billing_plan == product_code
    assert result.plan_expiration == period_end_date
    assert result.trial_start == trial_start
    assert result.trial_end == trial_end
    assert result.billing_period == billing_period


def test_get_subscription_details__premium__ok(mocker):

    # arrange
    period_end_date = timezone.now() + timedelta(days=30)
    period_end_date_timestamp = period_end_date.timestamp()
    price_stripe_id = 'price_123'
    product_code = 'premium'
    billing_period = BillingPeriod.MONTHLY
    product = create_test_product(code=product_code)
    create_test_recurring_price(
        stripe_id=price_stripe_id,
        product=product,
        period=billing_period
    )
    quantity = 11
    price_mock = mocker.Mock(id=price_stripe_id)
    item_mock = mocker.MagicMock(price=price_mock)
    create_price_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.mixins.'
        'StripeMixin._create_price'
    )
    subscription = {
        'current_period_end': period_end_date_timestamp,
        'quantity': quantity,
        'items': mocker.Mock(data=[item_mock]),
        'trial_start': None,
        'trial_end': None,
    }
    service = StripeMixin()

    # act
    result = service.get_subscription_details(subscription)

    # assert
    create_price_mock.assert_not_called()
    assert result.max_users == quantity
    assert result.quantity == quantity
    assert result.billing_plan == product_code
    assert result.plan_expiration == period_end_date
    assert result.trial_start is None
    assert result.trial_end is None
    assert result.billing_period == billing_period


def test_get_subscription_details__fractionalcoo__ok(mocker):

    # arrange
    product = create_test_product(code=BillingPlanType.FRACTIONALCOO)
    price_stripe_id = 'price_123'
    billing_period = BillingPeriod.WEEKLY
    create_test_recurring_price(
        product=product,
        stripe_id=price_stripe_id,
        period=billing_period
    )
    period_end_date = timezone.now() + timedelta(days=30)
    period_end_date_timestamp = period_end_date.timestamp()
    quantity = 11
    price_mock = mocker.Mock(id=price_stripe_id)
    item_mock = mocker.MagicMock(
        price=price_mock
    )
    create_price_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.mixins.'
        'StripeMixin._create_price'
    )
    subscription = {
        'current_period_end': period_end_date_timestamp,
        'quantity': quantity,
        'items': mocker.Mock(data=[item_mock]),
        'trial_start': None,
        'trial_end': None,
    }
    service = StripeMixin()

    # act
    result = service.get_subscription_details(subscription)

    # assert
    create_price_mock.assert_not_called()
    assert result.max_users == 1000
    assert result.quantity == quantity
    assert result.billing_plan == BillingPlanType.FRACTIONALCOO
    assert result.plan_expiration == period_end_date
    assert result.trial_start is None
    assert result.trial_end is None
    assert result.billing_period == billing_period


def test_get_subscription_details__fractionalcoo_trial__ok(mocker):

    # arrange
    trial_end = timezone.now() + timedelta(days=7)
    trial_end_timestamp = trial_end.timestamp()
    trial_start = timezone.now()
    trial_start_timestamp = trial_start.timestamp()
    period_end_date = timezone.now() + timedelta(days=15)
    period_end_date_timestamp = period_end_date.timestamp()
    product = create_test_product(code=BillingPlanType.FRACTIONALCOO)
    price_stripe_id = 'price_123'
    billing_period = BillingPeriod.YEARLY
    create_test_recurring_price(
        product=product,
        stripe_id=price_stripe_id,
        period=billing_period
    )
    quantity = 11
    price_mock = mocker.Mock(id=price_stripe_id)
    item_mock = mocker.MagicMock(price=price_mock)
    create_price_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.mixins.'
        'StripeMixin._create_price'
    )
    subscription = {
        'current_period_end': period_end_date_timestamp,
        'quantity': quantity,
        'items': mocker.Mock(data=[item_mock]),
        'trial_start': trial_start_timestamp,
        'trial_end': trial_end_timestamp,
    }
    service = StripeMixin()

    # act
    result = service.get_subscription_details(subscription)

    # assert
    create_price_mock.assert_not_called()
    assert result.max_users == 1000
    assert result.quantity == quantity
    assert result.billing_plan == BillingPlanType.FRACTIONALCOO
    assert result.plan_expiration == period_end_date
    assert result.trial_start == trial_start
    assert result.trial_end == trial_end
    assert result.billing_period == billing_period


def test_get_subscription_details__unlimited__ok(mocker):

    # arrange
    product = create_test_product(code=BillingPlanType.UNLIMITED)
    price_stripe_id = 'price_123'
    billing_period = BillingPeriod.YEARLY
    create_test_recurring_price(
        product=product,
        stripe_id=price_stripe_id,
        period=billing_period
    )
    period_end_date = timezone.now() + timedelta(days=30)
    period_end_date_timestamp = period_end_date.timestamp()
    quantity = 11
    price_mock = mocker.Mock(id=price_stripe_id)
    item_mock = mocker.MagicMock(
        price=price_mock
    )
    create_price_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.mixins.'
        'StripeMixin._create_price'
    )
    subscription = {
        'current_period_end': period_end_date_timestamp,
        'quantity': quantity,
        'items': mocker.Mock(data=[item_mock]),
        'trial_start': None,
        'trial_end': None,
    }
    service = StripeMixin()

    # act
    result = service.get_subscription_details(subscription)

    # assert
    create_price_mock.assert_not_called()
    assert result.max_users == 1000
    assert result.quantity == quantity
    assert result.billing_plan == BillingPlanType.UNLIMITED
    assert result.plan_expiration == period_end_date
    assert result.trial_start is None
    assert result.trial_end is None
    assert result.billing_period == billing_period


def test_get_subscription_details__unlimited_trial__ok(mocker):

    # arrange
    trial_end = timezone.now() + timedelta(days=7)
    trial_end_timestamp = trial_end.timestamp()
    trial_start = timezone.now()
    trial_start_timestamp = trial_start.timestamp()
    period_end_date = timezone.now() + timedelta(days=15)
    period_end_date_timestamp = period_end_date.timestamp()
    billing_period = BillingPeriod.DAILY
    product = create_test_product(code=BillingPlanType.UNLIMITED)
    price_stripe_id = 'price_123'
    create_test_recurring_price(
        product=product,
        stripe_id=price_stripe_id,
        period=billing_period
    )
    quantity = 11
    price_mock = mocker.Mock(id=price_stripe_id)
    item_mock = mocker.MagicMock(price=price_mock)
    create_price_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.mixins.'
        'StripeMixin._create_price'
    )
    subscription = {
        'current_period_end': period_end_date_timestamp,
        'quantity': quantity,
        'items': mocker.Mock(data=[item_mock]),
        'trial_start': trial_start_timestamp,
        'trial_end': trial_end_timestamp,
    }
    service = StripeMixin()

    # act
    result = service.get_subscription_details(subscription)

    # assert
    create_price_mock.assert_not_called()
    assert result.max_users == 1000
    assert result.quantity == quantity
    assert result.billing_plan == BillingPlanType.UNLIMITED
    assert result.plan_expiration == period_end_date
    assert result.trial_start == trial_start
    assert result.trial_end == trial_end
    assert result.billing_period == billing_period


def test_get_subscription_details__price_not_exist__create(mocker):

    # arrange
    price_stripe_id = 'price_123'
    period_end_date = timezone.now() + timedelta(days=30)
    period_end_date_timestamp = period_end_date.timestamp()
    quantity = 11
    price_mock = mocker.Mock(id=price_stripe_id)
    item_mock = mocker.MagicMock(
        price=price_mock
    )
    subscription = {
        'current_period_end': period_end_date_timestamp,
        'quantity': quantity,
        'items': mocker.Mock(data=[item_mock]),
        'trial_start': None,
        'trial_end': None,
    }

    billing_plan = BillingPlanType.UNLIMITED
    product = create_test_product(code=billing_plan)
    billing_period = BillingPeriod.YEARLY
    created_price_mock = mocker.Mock(
        product=product,
        billing_period=billing_period
    )
    create_price_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.mixins.'
        'StripeMixin._create_price',
        return_value=created_price_mock
    )
    service = StripeMixin()

    # act
    result = service.get_subscription_details(subscription)

    # assert
    create_price_mock.assert_called_once_with(price_mock)
    assert result.max_users == 1000
    assert result.quantity == quantity
    assert result.billing_plan == billing_plan
    assert result.plan_expiration == period_end_date
    assert result.trial_start is None
    assert result.trial_end is None
    assert result.billing_period == billing_period


def test_set_default_payment_method__existent_method__ok(mocker):

    # arrange
    customer_data = {'invoice_settings': {'default_payment_method': None}}
    customer_mock = mocker.MagicMock()
    customer_mock.__getitem__.side_effect = customer_data.__getitem__
    customer_mock.__setitem__.side_effect = customer_data.__setitem__
    customer_mock.save = mocker.Mock()

    subscription_data = {'default_payment_method': None}
    subscription_mock = mocker.MagicMock()
    subscription_mock.__getitem__.side_effect = subscription_data.__getitem__
    subscription_mock.__setitem__.side_effect = subscription_data.__setitem__
    subscription_mock.save = mocker.Mock()

    subscriptn_2_data = {'default_payment_method': None}
    subscriptn_2_mock = mocker.MagicMock()
    subscriptn_2_mock.__getitem__.side_effect = subscriptn_2_data.__getitem__
    subscriptn_2_mock.__setitem__.side_effect = subscriptn_2_data.__setitem__
    subscriptn_2_mock.save = mocker.Mock()

    subscription_list_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.mixins.'
        'stripe.Subscription.list',
        return_value=[subscription_mock, subscriptn_2_mock]
    )
    method_mock = mocker.Mock()
    method_mock.id = 13
    service = StripeMixin()

    # act
    result = service._set_default_payment_method(
        customer=customer_mock,
        method=method_mock
    )

    # assert
    assert result == method_mock
    assert (
        customer_mock['invoice_settings']['default_payment_method']
    ) == method_mock.id
    customer_mock.save.assert_called_once()
    subscription_list_mock.assert_called_once()
    assert subscription_mock['default_payment_method'] == method_mock.id
    subscription_mock.save.assert_called_once()
    assert subscriptn_2_mock['default_payment_method'] == method_mock.id
    subscriptn_2_mock.save.assert_called_once()


def test_set_default_payment_method__get_first_method__ok(mocker):

    # arrange
    customer_data = {'invoice_settings': {'default_payment_method': None}}
    customer_mock = mocker.MagicMock()
    customer_mock.__getitem__.side_effect = customer_data.__getitem__
    customer_mock.__setitem__.side_effect = customer_data.__setitem__
    customer_mock.save = mocker.Mock()

    subscription_data = {'default_payment_method': None}
    subscription_mock = mocker.MagicMock()
    subscription_mock.__getitem__.side_effect = subscription_data.__getitem__
    subscription_mock.__setitem__.side_effect = subscription_data.__setitem__
    subscription_mock.save = mocker.Mock()
    subscription_list_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.mixins.'
        'stripe.Subscription.list',
        return_value=[subscription_mock]
    )

    method_mock = mocker.Mock()
    method_mock.id = 13
    methods_mock = mocker.Mock()
    methods_mock.data = [method_mock]
    methods_list_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.mixins.'
        'stripe.PaymentMethod.list',
        return_value=methods_mock
    )
    service = StripeMixin()

    # act
    result = service._set_default_payment_method(customer=customer_mock)

    # assert
    assert result == method_mock
    subscription_list_mock.assert_called_once()
    methods_list_mock.assert_called_once_with(customer=customer_mock)
    assert (
        customer_mock['invoice_settings']['default_payment_method']
    ) == method_mock.id
    customer_mock.save.assert_called_once()
    assert subscription_mock['default_payment_method'] == method_mock.id
    subscription_mock.save.assert_called_once()


def test_set_default_payment_method__methods_not_exists__skip(mocker):

    # arrange
    customer_data = {'invoice_settings': {'default_payment_method': None}}
    customer_mock = mocker.MagicMock()
    customer_mock.__getitem__.side_effect = customer_data.__getitem__
    customer_mock.__setitem__.side_effect = customer_data.__setitem__
    customer_mock.save = mocker.Mock()

    subscription_data = {'default_payment_method': None}
    subscription_mock = mocker.MagicMock()
    subscription_mock.__getitem__.side_effect = subscription_data.__getitem__
    subscription_mock.__setitem__.side_effect = subscription_data.__setitem__
    subscription_mock.save = mocker.Mock()

    subscription_list_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.mixins.'
        'stripe.Subscription.list',
        return_value=[subscription_mock]
    )
    methods_mock = mocker.Mock()
    methods_mock.data = []
    methods_list_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.mixins.'
        'stripe.PaymentMethod.list',
        return_value=methods_mock
    )
    service = StripeMixin()

    # act
    result = service._set_default_payment_method(customer=customer_mock)

    # assert
    assert result is None
    subscription_list_mock.assert_not_called()
    methods_list_mock.assert_called_once_with(customer=customer_mock)
    assert customer_mock['invoice_settings']['default_payment_method'] is None
    customer_mock.save.assert_not_called()
    assert subscription_mock['default_payment_method'] is None
    subscription_mock.save.assert_not_called()


def test_get_current_payment_method__exists__ok(mocker):

    # arrange
    method_id = 'pm_123wae'
    customer = {'invoice_settings': {'default_payment_method': method_id}}
    method = mocker.Mock()
    get_payment_method_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.mixins.'
        'StripeMixin._get_payment_method',
        return_value=method
    )
    set_default_payment_method_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.mixins.'
        'StripeMixin._set_default_payment_method'
    )
    service = StripeMixin()

    # act
    result = service._get_current_payment_method(customer=customer)

    # assert
    assert result == method
    get_payment_method_mock.assert_called_once_with(method_id)
    set_default_payment_method_mock.assert_not_called()


def test_get_current_payment_method__not_exists__set(mocker):

    # arrange
    customer = {'invoice_settings': {'default_payment_method': None}}
    method = mocker.Mock()
    get_payment_method_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.mixins.'
        'StripeMixin._get_payment_method',
    )
    set_default_payment_method_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.mixins.'
        'StripeMixin._set_default_payment_method',
        return_value=method
    )
    service = StripeMixin()

    # act
    result = service._get_current_payment_method(customer=customer)

    # assert
    assert result == method
    get_payment_method_mock.assert_not_called()
    set_default_payment_method_mock.assert_called_once_with(
        customer=customer,
    )


def test_get_price_code__price_exists__code_not_changed():

    # arrange
    stripe_id = 'price_1NG8l0BM2UVM1VfGAlpUVQ5k'
    price_code = 'some_code'
    price = create_test_recurring_price(
        stripe_id=stripe_id,
        code=price_code
    )
    product_name = price.product.name
    interval = BillingPeriod.MONTHLY
    service = StripeMixin()

    # act
    result = service._get_price_code(
        stripe_id=stripe_id,
        code_parts=(product_name, interval)
    )

    # assert
    assert result == price_code


def test_get_price_code__new_price__ok():

    # arrange
    stripe_id = 'price_1NG8l0BM2UVM1VfGAlpUVQ5k'
    create_test_recurring_price()
    product_name = 'Some product'
    interval = BillingPeriod.YEARLY
    service = StripeMixin()

    # act
    result = service._get_price_code(
        stripe_id=stripe_id,
        code_parts=(product_name, interval)
    )

    # assert
    assert result == 'some_product_year'


def test_get_price_code__duplicate_code__return_with_hash(mocker):

    # arrange
    stripe_id = 'price_1NG8l0BM2UVM1VfGAlpUVQ5k'
    product_name = 'Some Product'
    interval = BillingPeriod.YEARLY
    product_code = f'some_product_{interval}'
    create_test_recurring_price(code=product_code)

    service = StripeMixin()
    salt = '!@#sdcxv'
    get_salt_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.mixins.get_salt',
        return_value=salt
    )

    # act
    result = service._get_price_code(
        stripe_id=stripe_id,
        code_parts=(product_name, interval)
    )

    # assert
    get_salt_mock.assert_called_once_with(6, exclude=("upper",))
    assert result == f'some_product_{interval}_{salt}'


def test_get_product_code__product_exists__code_not_changed():

    # arrange
    stripe_id = 'product_1NG8l0BM2UVM1VfGAlpUVQ5k'
    product_code = 'some_code'
    product_name = 'Some name'
    create_test_product(
        stripe_id=stripe_id,
        code=product_code,
        name=product_name
    )
    service = StripeMixin()

    # act
    result = service._get_product_code(
        stripe_id=stripe_id,
        name=product_name,
    )

    # assert
    assert result == product_code


def test_get_product_code__new_product__ok():

    # arrange
    stripe_id = 'product_1NG8l0BM2UVM1VfGAlpUVQ5k'
    product_name = 'Some name'

    service = StripeMixin()

    # act
    result = service._get_product_code(
        stripe_id=stripe_id,
        name=product_name,
    )

    # assert
    assert result == 'some_name'


def test_get_product_code__duplicate_code__return_with_hash(mocker):

    # arrange
    stripe_id = 'product_1NG8l0BM2UVM1VfGAlpUVQ5k'
    product_code = 'some_name'
    product_name = 'Some name'
    create_test_product(code=product_code)
    salt = '!@#sdcxv'
    get_salt_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.mixins.get_salt',
        return_value=salt
    )
    service = StripeMixin()

    # act
    result = service._get_product_code(
        stripe_id=stripe_id,
        name=product_name,
    )

    # assert
    get_salt_mock.assert_called_once_with(6, exclude=("upper",))
    assert result == f'some_name_{salt}'


def test_get_idempotency_key__no_kwargs__ok():

    # arrange
    service = StripeMixin()

    # act
    value = service._get_idempotency_key()

    # assert
    assert len(value) == 40


def test_get_idempotency_key__same_kwargs__same_result():

    # arrange
    service = StripeMixin()
    data = {
        'key': [{'c': 1, 'a': 'cad'}],
        'avd': 'str',
        '0': None
    }
    value_1 = service._get_idempotency_key(**data)

    # act
    value_2 = service._get_idempotency_key(**data)

    # assert
    assert value_1 == value_2


def test_create_price__recurring__ok(mocker):

    # arrange
    product = create_test_product()
    stripe_id = 'price_1NG8l0BM2UVM1VfGAlpUVQ5k'
    is_active = False
    interval = BillingPeriod.DAILY
    unit_amount = 100
    trial_days = 5
    max_quantity = 9999
    currency = 'usd'
    data = {
      "id": "evt_1NG8l0BM2UVM1VfGZo5GSCLu",
      "object": "event",
      "api_version": "2022-11-15",
      "created": 1686092022,
      "data": {
        "object": {
          "id": stripe_id,
          "object": "price",
          "active": is_active,
          "billing_scheme": "per_unit",
          "created": 1686092022,
          "currency": currency,
          "custom_unit_amount": None,
          "livemode": False,
          "lookup_key": None,
          "metadata": {
          },
          "nickname": None,
          "product": product.stripe_id,
          "recurring": {
            "aggregate_usage": None,
            "interval": interval,
            "interval_count": 1,
            "trial_period_days": trial_days,
            "usage_type": "licensed"
          },
          "tax_behavior": "unspecified",
          "tiers_mode": None,
          "transform_quantity": None,
          "type": PriceType.RECURRING,
          "unit_amount": unit_amount,
          "unit_amount_decimal": "100"
        }
      },
      "livemode": False,
      "pending_webhooks": 1,
      "request": {
        "id": "req_7nqnxNbq2uZMqX",
        "idempotency_key": "d7d2b29b-f591-4581-8670-8d90d2f2f394"
      },
      "type": "price.created"
    }
    event = stripe.Event.construct_from(
        values=data,
        key='!!@#'
    )
    service = StripeMixin()
    price_code = 'some_code'
    get_subscription_details_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.mixins.'
        'StripeMixin._get_price_code',
        return_value=price_code
    )

    # act
    service._create_price(event.data['object'])

    # assert
    get_subscription_details_mock.assert_called_once_with(
        stripe_id=stripe_id,
        code_parts=(product.name, interval)
    )
    assert Price.objects.filter(
        product=product,
        status=PriceStatus.INACTIVE,
        name='Premium day',
        code=price_code,
        stripe_id=stripe_id,
        max_quantity=max_quantity,
        min_quantity=0,
        price_type=PriceType.RECURRING,
        price=unit_amount,
        trial_days=trial_days,
        billing_period=interval,
        currency=currency
    ).exists()


def test_create_price__one_time__ok(mocker):

    # arrange
    product = create_test_product()
    stripe_id = 'price_1NG8l0BM2UVM1VfGAlpUVQ5k'
    is_active = True
    unit_amount = 1000
    max_quantity = 1
    currency = 'eur'
    data = {
      "id": "evt_1NG8l0BM2UVM1VfGZo5GSCLu",
      "object": "event",
      "api_version": "2022-11-15",
      "created": 1686092022,
      "data": {
        "object": {
          "id": stripe_id,
          "object": "price",
          "active": is_active,
          "billing_scheme": "per_unit",
          "created": 1686092022,
          "currency": currency,
          "custom_unit_amount": None,
          "livemode": False,
          "lookup_key": None,
          "metadata": {
          },
          "nickname": None,
          "product": product.stripe_id,
          "recurring": None,
          "tax_behavior": "unspecified",
          "tiers_mode": None,
          "transform_quantity": None,
          "type": PriceType.ONE_TIME,
          "unit_amount": unit_amount,
          "unit_amount_decimal": "100"
        }
      },
      "livemode": False,
      "pending_webhooks": 1,
      "request": {
        "id": "req_7nqnxNbq2uZMqX",
        "idempotency_key": "d7d2b29b-f591-4581-8670-8d90d2f2f394"
      },
      "type": "price.created"
    }
    event = stripe.Event.construct_from(
        values=data,
        key='!!@#'
    )
    service = StripeMixin()
    price_code = 'some_code'
    get_subscription_details_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.mixins.'
        'StripeMixin._get_price_code',
        return_value=price_code
    )

    # act
    service._create_price(event.data['object'])

    # assert
    get_subscription_details_mock.assert_called_once_with(
        stripe_id=stripe_id,
        code_parts=(product.name,)
    )
    assert Price.objects.filter(
        product=product,
        status=PriceStatus.ACTIVE,
        name='Premium',
        code=price_code,
        stripe_id=stripe_id,
        max_quantity=max_quantity,
        min_quantity=0,
        price_type=PriceType.ONE_TIME,
        price=unit_amount,
        trial_days=None,
        billing_period=None,
        currency=currency
    ).exists()


def test_get_account_for_subscription__main_with_metadata__ok(
    mocker
):

    # arrange
    account = create_test_account(lease_level=LeaseLevel.STANDARD)
    create_test_account(
        lease_level=LeaseLevel.TENANT,
        master_account=account
    )
    subscription_mock = mocker.Mock(metadata={'account_id': str(account.id)})
    service = StripeMixin()

    # act
    result = service._get_account_for_subscription(
        account=account,
        subscription=subscription_mock
    )

    # assert
    assert result == account


def test_get_account_for_subscription__main_without_metadata__ok(
    mocker
):

    # arrange
    account = create_test_account(lease_level=LeaseLevel.STANDARD)
    create_test_account(
        lease_level=LeaseLevel.TENANT,
        master_account=account
    )
    subscription_mock = mocker.Mock(metadata={})
    service = StripeMixin()

    # act
    result = service._get_account_for_subscription(
        account=account,
        subscription=subscription_mock
    )

    # assert
    assert result == account


def test_get_account_for_subscription__tenant__ok(
    mocker
):

    # arrange
    account = create_test_account(lease_level=LeaseLevel.STANDARD)
    tenant = create_test_account(
        lease_level=LeaseLevel.TENANT,
        master_account=account,
        name='Tenant'
    )
    subscription_mock = mocker.Mock(metadata={'account_id': str(tenant.id)})
    service = StripeMixin()

    # act
    result = service._get_account_for_subscription(
        account=account,
        subscription=subscription_mock
    )

    # assert
    assert result == tenant


def test_get_account_for_subscription__invalid_metadata__raise(mocker):

    # arrange
    account = create_test_account(lease_level=LeaseLevel.STANDARD)
    tenant = create_test_account(
        lease_level=LeaseLevel.TENANT,
        master_account=account
    )
    metadata = {'account_id': f'{tenant.id}a'}
    subscription_mock = mocker.Mock(metadata=metadata)
    service = StripeMixin()

    # act
    with pytest.raises(NotFoundAccountForSubscription) as ex:
        service._get_account_for_subscription(
            account=account,
            subscription=subscription_mock
        )

    # assert
    assert ex.value.details['account_id'] == account.id
    assert ex.value.details['subs_metadata'] == metadata


def test_get_account_for_subscription__not_found__raise(mocker):

    # arrange
    account = create_test_account(lease_level=LeaseLevel.STANDARD)
    tenant = create_test_account(lease_level=LeaseLevel.TENANT)
    metadata = {'account_id': str(tenant.id)}
    subscription_mock = mocker.Mock(metadata=metadata)
    service = StripeMixin()

    # act
    with pytest.raises(NotFoundAccountForSubscription) as ex:
        service._get_account_for_subscription(
            account=account,
            subscription=subscription_mock
        )

    # assert
    assert ex.value.message == messages.MSG_BL_0017
    assert ex.value.details['account_id'] == account.id
    assert ex.value.details['subs_metadata'] == metadata
