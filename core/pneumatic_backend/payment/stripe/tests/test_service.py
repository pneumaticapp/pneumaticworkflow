import pytest
import stripe
from django.utils import timezone
from datetime import timedelta
from pneumatic_backend.authentication.enums import (
    AuthTokenType
)
from pneumatic_backend.accounts.enums import (
    BillingPlanType,
    LeaseLevel,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_account,
    create_test_user,
)
from pneumatic_backend.payment.enums import (
    PriceStatus
)
from pneumatic_backend.payment.stripe.exceptions import (
    CardError,
    PaymentError,
    DecreaseSubscription,
    MultipleSubscriptionsNotAllowed,
    ChangeCurrencyDisallowed,
    MaxQuantityReached,
    MinQuantityReached,
    SubsMaxQuantityReached,
    SubsMinQuantityReached,
    UnsupportedPlan,
    PurchaseArchivedPrice,
    SubscriptionNotExist,
)
from pneumatic_backend.payment.stripe.service import StripeService
from pneumatic_backend.payment.services.account import (
    AccountSubscriptionService
)
from pneumatic_backend.payment.tests.fixtures import (
    create_test_recurring_price,
    create_test_invoice_price,
    create_test_product,
)
from pneumatic_backend.payment.stripe.entities import (
    TokenSubscriptionData,
    PurchaseItem,
)
from pneumatic_backend.payment.stripe.tokens import ConfirmToken
from pneumatic_backend.payment import messages
from pneumatic_backend.accounts.services import AccountService


pytestmark = pytest.mark.django_db


def test_init__master_subscription__ok(mocker):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    is_superuser = True
    auth_type = AuthTokenType.API
    subscription_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=subscription_mock
    )
    method_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method',
        return_value=method_mock
    )
    account_subscription_service_init_mock = mocker.patch.object(
        AccountSubscriptionService,
        attribute='__init__',
        return_value=None
    )
    customer_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
        return_value=customer_mock
    )

    # act
    service = StripeService(
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # assert
    assert service.user == user
    assert service.account == account
    assert service.subscription_account == account
    assert service.subscription_owner == user
    assert service.auth_type == auth_type
    assert service.is_superuser == is_superuser
    assert service.customer == customer_mock
    assert service.subscription == subscription_mock
    assert service.payment_method == method_mock
    account_subscription_service_init_mock.assert_called_once_with(
        instance=account,
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type
    )


def test_init__tenant_subscription__ok(mocker):

    # arrange
    master_account = create_test_account(lease_level=LeaseLevel.STANDARD)
    user = create_test_user(account=master_account, email='owner@test.test')
    tenant = create_test_account(
        lease_level=LeaseLevel.TENANT,
        master_account=master_account,
        name='Tenant'
    )
    tenant_owner = create_test_user(account=tenant)
    is_superuser = True
    auth_type = AuthTokenType.API
    subscription_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=subscription_mock
    )
    method_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method',
        return_value=method_mock
    )
    account_subscription_service_init_mock = mocker.patch.object(
        AccountSubscriptionService,
        attribute='__init__',
        return_value=None
    )
    customer_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
        return_value=customer_mock
    )

    # act
    service = StripeService(
        user=user,
        subscription_account=tenant,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # assert
    assert service.user == user
    assert service.account == master_account
    assert service.subscription_account == tenant
    assert service.subscription_owner == tenant_owner
    assert service.auth_type == auth_type
    assert service.is_superuser == is_superuser
    assert service.customer == customer_mock
    assert service.subscription == subscription_mock
    assert service.payment_method == method_mock
    account_subscription_service_init_mock.assert_called_once_with(
        instance=tenant,
        user=tenant_owner,
        is_superuser=is_superuser,
        auth_type=auth_type
    )


def test_get_or_create_customer__ok(mocker):

    # arrange
    # init mock
    customer_stripe_id = "cus_testNx9XuHa4xteob3"
    account = create_test_account(stripe_id=customer_stripe_id)
    user = create_test_user(account=account)
    is_superuser = True
    auth_type = AuthTokenType.API
    subscription_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=subscription_mock
    )
    method_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method',
        return_value=method_mock
    )
    mocker.patch.object(
        AccountSubscriptionService,
        attribute='__init__',
        return_value=None
    )
    # end init mock

    customer_mock = mocker.Mock()
    get_customer_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_customer',
        return_value=customer_mock
    )
    create_customer_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'stripe.Customer.create',
    )
    update_customer_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService.update_customer'
    )
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    account_service_update_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'AccountService.partial_update'
    )

    # act
    service = StripeService(
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # assert
    get_customer_mock.assert_called_once_with(customer_stripe_id)
    assert service.customer == customer_mock
    create_customer_mock.assert_not_called()
    update_customer_mock.assert_not_called()
    account_service_init_mock.assert_not_called()
    account_service_update_mock.assert_not_called()


def test_get_or_create_customer__get_by_email__ok(mocker):

    # arrange
    # init mock
    customer_stripe_id = "cus_testNx9XuHa4xteob3"
    account = create_test_account(stripe_id=customer_stripe_id)
    user = create_test_user(account=account)
    is_superuser = True
    auth_type = AuthTokenType.API
    subscription_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=subscription_mock
    )
    method_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method',
        return_value=method_mock
    )
    mocker.patch.object(
        AccountSubscriptionService,
        attribute='__init__',
        return_value=None
    )
    # end init mock

    get_customer_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_customer',
        return_value=None
    )
    customer_mock = mocker.Mock(id=123)
    get_customer_by_email_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_customer_by_email',
        return_value=customer_mock
    )
    create_customer_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'stripe.Customer.create',
    )
    update_customer_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService.update_customer'
    )
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    account_service_update_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'AccountService.partial_update'
    )

    # act
    service = StripeService(
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # assert
    assert service.customer == customer_mock
    get_customer_mock.assert_called_once_with(customer_stripe_id)
    create_customer_mock.assert_not_called()
    update_customer_mock.assert_called_once()
    get_customer_by_email_mock.assert_called_once_with(user.email)
    account_service_init_mock.assert_called_once_with(
        user=user,
        instance=account,
        is_superuser=is_superuser,
        auth_type=auth_type
    )
    account_service_update_mock.assert_called_once_with(
        stripe_id=customer_mock.id,
        force_save=True
    )


def test_get_or_create_customer__not_exist_customer__create(mocker):

    # arrange
    # init mock
    account = create_test_account(stripe_id=None)
    account_owner = create_test_user(
        account=account,
        email='owner@test.test',
        phone='12223334455',
        first_name='Don',
        last_name='Macman',
        is_account_owner=True,
    )
    user = create_test_user(
        account=account,
        is_account_owner=False
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    subscription_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=subscription_mock
    )
    method_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method',
        return_value=method_mock
    )
    mocker.patch.object(
        AccountSubscriptionService,
        attribute='__init__',
        return_value=None
    )
    # end init mock

    get_customer_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_customer',
        return_value=None
    )
    get_customer_by_email_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_customer_by_email',
        return_value=None
    )
    customer_mock = mocker.Mock(id=123)
    create_customer_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'stripe.Customer.create',
        return_value=customer_mock
    )
    update_customer_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService.update_customer'
    )
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    account_service_update_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'AccountService.partial_update'
    )

    # act
    service = StripeService(
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # assert
    assert service.customer == customer_mock
    get_customer_mock.assert_not_called()
    get_customer_by_email_mock.assert_called_once_with(
        account_owner.email
    )
    create_customer_mock.assert_called_once_with(
        email=account_owner.email,
        name=account.name,
        phone=account_owner.phone,
        description=f'{account_owner.first_name} {account_owner.last_name}'
    )
    update_customer_mock.assert_not_called()
    account_service_init_mock.assert_called_once_with(
        user=user,
        instance=account,
        is_superuser=is_superuser,
        auth_type=auth_type
    )
    account_service_update_mock.assert_called_once_with(
        stripe_id=customer_mock.id,
        force_save=True
    )


def test_get_current_subscription__ok(mocker):

    # arrange
    # init
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
        plan_expiration=timezone.now() + timedelta(days=10),
        payment_card_provided=True
    )
    user = create_test_user(account=account)
    is_superuser = True
    auth_type = AuthTokenType.API
    customer_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
        return_value=customer_mock
    )
    method_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method',
        return_value=method_mock
    )
    mocker.patch.object(
        AccountSubscriptionService,
        attribute='__init__',
        return_value=None
    )
    # end init

    subscription_mock = mocker.Mock()
    get_subscription_for_account_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_subscription_for_account',
        return_value=subscription_mock
    )
    account_subscription_service_create_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'AccountSubscriptionService.create'
    )
    account_subscription_service_expired_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'AccountSubscriptionService.expired'
    )

    # act
    service = StripeService(
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # assert
    assert service.subscription == subscription_mock
    get_subscription_for_account_mock.assert_called_once_with(
        customer=customer_mock,
        subscription_account=account
    )
    account_subscription_service_create_mock.assert_not_called()
    account_subscription_service_expired_mock.assert_not_called()


def test_get_current_subscription__create__ok(mocker):

    # arrange
    # init
    payment_card_provided = True
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
        plan_expiration=timezone.now() - timedelta(days=10),
        payment_card_provided=payment_card_provided
    )
    user = create_test_user(account=account)
    is_superuser = True
    auth_type = AuthTokenType.API
    customer_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
        return_value=customer_mock
    )
    method_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method',
        return_value=method_mock
    )
    mocker.patch.object(
        AccountSubscriptionService,
        attribute='__init__',
        return_value=None
    )
    # end init

    subscription_mock = mocker.Mock()
    get_subscription_for_account_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_subscription_for_account',
        return_value=subscription_mock
    )
    account_subscription_service_create_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'AccountSubscriptionService.create'
    )
    account_subscription_service_expired_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'AccountSubscriptionService.expired'
    )
    subscription_details_mock = mocker.Mock()
    get_subscription_details_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService.get_subscription_details',
        return_value=subscription_details_mock
    )

    # act
    service = StripeService(
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # assert
    assert service.subscription == subscription_mock
    get_subscription_for_account_mock.assert_called_once_with(
        customer=customer_mock,
        subscription_account=account
    )
    get_subscription_details_mock.assert_called_once_with(
        subscription_mock
    )
    account_subscription_service_create_mock.assert_called_once_with(
        details=subscription_details_mock,
        payment_card_provided=payment_card_provided
    )
    account_subscription_service_expired_mock.assert_not_called()


def test_get_current_subscription__expire__ok(mocker):

    # arrange
    # init
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
        plan_expiration=timezone.now() + timedelta(days=10),
        payment_card_provided=True
    )
    user = create_test_user(account=account)
    is_superuser = True
    auth_type = AuthTokenType.API
    customer_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
        return_value=customer_mock
    )
    method_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method',
        return_value=method_mock
    )
    mocker.patch.object(
        AccountSubscriptionService,
        attribute='__init__',
        return_value=None
    )
    # end init

    get_subscription_for_account_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_subscription_for_account',
        return_value=None
    )
    account_subscription_service_create_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'AccountSubscriptionService.create'
    )
    account_subscription_service_expired_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'AccountSubscriptionService.expired'
    )
    now_date = timezone.now()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.timezone.now',
        return_value=now_date
    )

    # act
    service = StripeService(
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # assert
    assert service.subscription is None
    get_subscription_for_account_mock.assert_called_once_with(
        customer=customer_mock,
        subscription_account=account
    )
    account_subscription_service_create_mock.assert_not_called()
    account_subscription_service_expired_mock.assert_called_once_with(
        plan_expiration=now_date
    )


def test_get_current_subscription__tenant_create__ok(mocker):

    # arrange
    # init
    master_account = create_test_account(
        lease_level=LeaseLevel.STANDARD
    )
    user = create_test_user(account=master_account)
    tenant_name = 'some tenant name'
    tenant_account = create_test_account(
        lease_level=LeaseLevel.TENANT,
        master_account=master_account,
        name='tenant',
        tenant_name=tenant_name,
        plan=BillingPlanType.UNLIMITED,
        plan_expiration=timezone.now() - timedelta(days=10),
        payment_card_provided=True
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    customer_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
        return_value=customer_mock
    )
    method_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method',
        return_value=method_mock
    )
    mocker.patch.object(
        AccountSubscriptionService,
        attribute='__init__',
        return_value=None
    )
    # end init

    subscription_mock = mocker.Mock()
    get_subscription_for_account_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_subscription_for_account',
        return_value=subscription_mock
    )
    account_subscription_service_create_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'AccountSubscriptionService.create'
    )
    account_subscription_service_expired_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'AccountSubscriptionService.expired'
    )
    subscription_details_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService.get_subscription_details',
        return_value=subscription_details_mock
    )

    # act
    service = StripeService(
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
        subscription_account=tenant_account
    )

    # assert
    assert service.subscription == subscription_mock
    get_subscription_for_account_mock.assert_called_once_with(
        customer=customer_mock,
        subscription_account=tenant_account
    )
    account_subscription_service_create_mock.assert_called_once_with(
        details=subscription_details_mock,
        payment_card_provided=master_account.payment_card_provided,
    )
    account_subscription_service_expired_mock.assert_not_called()


def test_get_current_payment_method__ok(mocker):

    # arrange
    # init
    account = create_test_account(
        payment_card_provided=True
    )
    user = create_test_user(account=account)
    is_superuser = True
    auth_type = AuthTokenType.API
    customer_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
        return_value=customer_mock
    )
    subscription_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=subscription_mock
    )
    mocker.patch.object(
        AccountSubscriptionService,
        attribute='__init__',
        return_value=None
    )
    # end init

    payment_method_mock = mocker.Mock()
    get_current_payment_method_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.mixins.'
        'StripeMixin._get_current_payment_method',
        return_value=payment_method_mock
    )
    payment_card_provided_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'AccountSubscriptionService.payment_card_provided'
    )

    # act
    service = StripeService(
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # assert
    assert service.payment_method == payment_method_mock
    get_current_payment_method_mock.assert_called_once_with(
        customer=customer_mock,
    )
    payment_card_provided_mock.assert_not_called()


def test_get_current_payment_method__enable__ok(mocker):

    # arrange
    # init
    account = create_test_account(
        payment_card_provided=False
    )
    user = create_test_user(account=account)
    is_superuser = True
    auth_type = AuthTokenType.API
    customer_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
        return_value=customer_mock
    )
    subscription_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=subscription_mock
    )
    mocker.patch.object(
        AccountSubscriptionService,
        attribute='__init__',
        return_value=None
    )
    # end init

    payment_method_mock = mocker.Mock()
    get_current_payment_method_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.mixins.'
        'StripeMixin._get_current_payment_method',
        return_value=payment_method_mock
    )
    payment_card_provided_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'AccountSubscriptionService.payment_card_provided'
    )

    # act
    service = StripeService(
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # assert
    assert service.payment_method == payment_method_mock
    get_current_payment_method_mock.assert_called_once_with(
        customer=customer_mock,
    )
    payment_card_provided_mock.assert_called_once_with(value=True)


def test_get_current_payment_method__disable__ok(mocker):

    # arrange
    # init
    account = create_test_account(
        payment_card_provided=True
    )
    user = create_test_user(account=account)
    is_superuser = True
    auth_type = AuthTokenType.API
    customer_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
        return_value=customer_mock
    )
    subscription_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=subscription_mock
    )
    mocker.patch.object(
        AccountSubscriptionService,
        attribute='__init__',
        return_value=None
    )
    # end init

    get_current_payment_method_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.mixins.'
        'StripeMixin._get_current_payment_method',
        return_value=None
    )
    payment_card_provided_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'AccountSubscriptionService.payment_card_provided'
    )

    # act
    service = StripeService(
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # assert
    assert service.payment_method is None
    get_current_payment_method_mock.assert_called_once_with(
        customer=customer_mock,
    )
    payment_card_provided_mock.assert_called_once_with(value=False)


def test_get_confirm_token__ok(mocker):

    # arrange

    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer'
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription'
    )
    # end mock init

    customer_stripe_id = "cus_testNx9XuHa4xteob3"
    account = create_test_account(stripe_id=customer_stripe_id)
    user = create_test_user(account=account)
    is_superuser = True
    auth_type = AuthTokenType.API

    service = StripeService(
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type
    )

    # act
    result = service._get_confirm_token()

    # assert
    assert isinstance(result, ConfirmToken)
    assert result.payload['auth_type'] == auth_type
    assert result.payload['is_superuser'] == is_superuser
    assert result.payload['account_id'] == account.id
    assert result.payload['user_id'] == user.id
    assert 'subscription' not in result.payload.keys()


def test_get_confirm_token__with_subscription__ok(mocker):

    # arrange

    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer'
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription'
    )
    # end mock init

    customer_stripe_id = "cus_testNx9XuHa4xteob3"
    account = create_test_account(stripe_id=customer_stripe_id)
    user = create_test_user(account=account)
    is_superuser = True
    auth_type = AuthTokenType.API
    subscription_data = mocker.Mock()

    service = StripeService(
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type
    )

    # act
    result = service._get_confirm_token(
        subscription_data=subscription_data
    )

    # assert
    assert isinstance(result, ConfirmToken)
    assert result.payload['auth_type'] == auth_type
    assert result.payload['is_superuser'] == is_superuser
    assert result.payload['account_id'] == account.id
    assert result.payload['user_id'] == user.id
    assert result.payload['subscription'] == subscription_data


def test_get_success_url_with_token__without_query_params__ok(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer'
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription'
    )
    # end mock init

    customer_stripe_id = "cus_testNx9XuHa4xteob3"
    account = create_test_account(stripe_id=customer_stripe_id)
    user = create_test_user(account=account)
    url = 'https://some.site/success'
    subscription_data = mocker.Mock()
    token = ConfirmToken()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_confirm_token',
        return_value=token
    )

    service = StripeService(user=user)

    # act
    result = service._get_success_url_with_token(
        url=url,
        subscription_data=subscription_data
    )

    # assert
    assert result == f'{url}?token={token}'


def test_get_success_url_with_token__with_query_params__ok(mocker):

    # arrange

    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer'
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription'
    )
    # end mock init

    customer_stripe_id = "cus_testNx9XuHa4xteob3"
    account = create_test_account(stripe_id=customer_stripe_id)
    user = create_test_user(account=account)
    url = 'https://some.site/success?param=value'
    subscription_data = mocker.Mock()
    token = ConfirmToken()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_confirm_token',
        return_value=token
    )

    service = StripeService(user=user)

    # act
    result = service._get_success_url_with_token(
        url=url,
        subscription_data=subscription_data
    )

    # assert
    assert result == f'{url}&token={token}'


def test_create_subscription__trial_not_ended__ok(mocker):

    # arrange

    # mock init
    customer_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
        return_value=customer_mock
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=None
    )
    # end mock init

    customer_stripe_id = "cus_testNx9XuHa4xteob3"
    account = create_test_account(
        stripe_id=customer_stripe_id,
        trial_ended=False
    )
    user = create_test_user(account=account)
    quantity = 10
    trial_days = 11
    price_stripe_id = 'pr_12DSADasd'

    item = mocker.Mock()
    item.quantity = quantity
    item.price = mocker.Mock(
        trial_days=trial_days,
        stripe_id=price_stripe_id
    )
    invoice_item_price_stripe_id = 'pr_iwdasd'
    invoice_item_mock = mocker.Mock()
    invoice_item_mock.quantity = 1
    invoice_item_mock.price = mocker.Mock(
        stripe_id=invoice_item_price_stripe_id
    )
    invoice_items = [invoice_item_mock]
    subscription_mock = mocker.Mock()
    subscription_create_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'stripe.Subscription.create',
        return_value=subscription_mock
    )
    idempotency_key = '12312asdw'
    get_idempotency_key_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_idempotency_key',
        return_value=idempotency_key
    )
    date = timezone.now()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.timezone.now',
        return_value=date
    )
    subscription_details_mock = mocker.Mock()
    get_subscription_details_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService.get_subscription_details',
        return_value=subscription_details_mock
    )

    service = StripeService(user=user)
    service.subscription_service = mocker.Mock(create=mocker.Mock())

    # act
    service._create_subscription(
        item=item,
        invoice_items=invoice_items
    )

    # assert
    items = [
        {
            "price": price_stripe_id,
            "quantity": quantity,
        }
    ]
    add_invoice_items = [
        {
            "price": invoice_item_price_stripe_id,
            "quantity": 1,
        }
    ]
    subscription_create_mock.assert_called_once_with(
        customer=customer_mock,
        items=items,
        add_invoice_items=add_invoice_items,
        trial_period_days=trial_days,
        idempotency_key=idempotency_key,
        metadata={'account_id': account.id},
        description='Main'
    )
    get_idempotency_key_mock.assert_called_once_with(
        account_id=account.id,
        items=items,
        add_invoice_items=add_invoice_items,
        trial_period_days=trial_days,
        stripe_id=customer_stripe_id,
        date=date.strftime('%Y-%m-%dT%H:%M')
    )
    get_subscription_details_mock.assert_called_once_with(subscription_mock)
    service.subscription_service.create.assert_called_once_with(
        details=subscription_details_mock,
        payment_card_provided=True,
    )


def test_create_subscription__trial_ended__ok(mocker):

    # arrange
    # mock init
    customer_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
        return_value=customer_mock
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=None
    )
    # end mock init

    customer_stripe_id = "cus_testNx9XuHa4xteob3"
    account = create_test_account(
        stripe_id=customer_stripe_id,
        trial_ended=True
    )
    user = create_test_user(account=account)
    quantity = 10
    price_stripe_id = 'pr_12DSADasd'

    item = mocker.Mock()
    item.quantity = quantity
    item.price = mocker.Mock(
        stripe_id=price_stripe_id
    )
    subscription_mock = mocker.Mock()
    subscription_create_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'stripe.Subscription.create',
        return_value=subscription_mock
    )
    idempotency_key = '12312asdw'
    get_idempotency_key_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_idempotency_key',
        return_value=idempotency_key
    )
    date = timezone.now()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.timezone.now',
        return_value=date
    )
    subscription_details_mock = mocker.Mock()
    get_subscription_details_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService.get_subscription_details',
        return_value=subscription_details_mock
    )

    service = StripeService(user=user)
    service.subscription_service = mocker.Mock(create=mocker.Mock())

    # act
    service._create_subscription(
        item=item,
        invoice_items=[]
    )

    # assert
    items = [
        {
            "price": price_stripe_id,
            "quantity": quantity,
        }
    ]
    subscription_create_mock.assert_called_once_with(
        customer=customer_mock,
        items=items,
        add_invoice_items=[],
        trial_period_days=None,
        idempotency_key=idempotency_key,
        metadata={'account_id': account.id},
        description='Main'
    )
    get_idempotency_key_mock.assert_called_once_with(
        account_id=account.id,
        items=items,
        add_invoice_items=[],
        trial_period_days=None,
        stripe_id=customer_stripe_id,
        date=date.strftime('%Y-%m-%dT%H:%M')
    )
    get_subscription_details_mock.assert_called_once_with(subscription_mock)
    service.subscription_service.create.assert_called_once_with(
        details=subscription_details_mock,
        payment_card_provided=True,
    )


def test_create_subscription__tenant_subscription__ok(mocker):

    # arrange

    # mock init
    customer_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
        return_value=customer_mock
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=None
    )
    # end mock init

    customer_stripe_id = "cus_testNx9XuHa4xteob3"
    master_account = create_test_account(
        trial_ended=False,
        lease_level=LeaseLevel.STANDARD
    )
    user = create_test_user(account=master_account)
    tenant_name = 'some teant name'
    tenant_account = create_test_account(
        stripe_id=customer_stripe_id,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account,
        name='tenant',
        tenant_name=tenant_name
    )
    quantity = 10
    trial_days = 11
    price_stripe_id = 'pr_12DSADasd'

    item = mocker.Mock()
    item.quantity = quantity
    item.price = mocker.Mock(
        trial_days=trial_days,
        stripe_id=price_stripe_id
    )
    invoice_item_price_stripe_id = 'pr_iwdasd'
    invoice_item_mock = mocker.Mock()
    invoice_item_mock.quantity = 1
    invoice_item_mock.price = mocker.Mock(
        stripe_id=invoice_item_price_stripe_id
    )
    invoice_items = [invoice_item_mock]
    subscription_mock = mocker.Mock()
    subscription_create_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'stripe.Subscription.create',
        return_value=subscription_mock
    )
    idempotency_key = '12312asdw'
    get_idempotency_key_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_idempotency_key',
        return_value=idempotency_key
    )
    date = timezone.now()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.timezone.now',
        return_value=date
    )
    subscription_details_mock = mocker.Mock()
    get_subscription_details_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService.get_subscription_details',
        return_value=subscription_details_mock
    )

    service = StripeService(
        user=user,
        subscription_account=tenant_account
    )
    service.subscription_service = mocker.Mock(create=mocker.Mock())

    # act
    service._create_subscription(
        item=item,
        invoice_items=invoice_items
    )

    # assert
    items = [
        {
            "price": price_stripe_id,
            "quantity": quantity,
        }
    ]
    add_invoice_items = [
        {
            "price": invoice_item_price_stripe_id,
            "quantity": 1,
        }
    ]
    subscription_create_mock.assert_called_once_with(
        customer=customer_mock,
        items=items,
        add_invoice_items=add_invoice_items,
        trial_period_days=trial_days,
        idempotency_key=idempotency_key,
        metadata={'account_id': tenant_account.id},
        description=tenant_name
    )
    get_idempotency_key_mock.assert_called_once_with(
        account_id=tenant_account.id,
        items=items,
        add_invoice_items=add_invoice_items,
        trial_period_days=trial_days,
        stripe_id=customer_stripe_id,
        date=date.strftime('%Y-%m-%dT%H:%M')
    )
    get_subscription_details_mock.assert_called_once_with(subscription_mock)
    service.subscription_service.create.assert_called_once_with(
        details=subscription_details_mock,
        payment_card_provided=True,
    )


def test_update_subscription__same_price__ok(mocker):

    # arrange
    # mock init
    customer_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
        return_value=customer_mock
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )

    # old subscription data
    old_price_id = 'price_1213ad'
    old_sub_price_mock = mocker.Mock(id=old_price_id)
    old_item_mock = mocker.MagicMock(
        id=old_price_id,
        price=old_sub_price_mock
    )
    old_sub_data = {'items': mocker.Mock(data=[old_item_mock])}
    old_sub_id = 'sub_123AD'
    old_subs_mock = mocker.MagicMock(id=old_sub_id)
    old_subs_mock.__getitem__.side_effect = old_sub_data.__getitem__
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=old_subs_mock
    )

    customer_stripe_id = "cus_testNx9XuHa4xteob3"
    account = create_test_account(
        stripe_id=customer_stripe_id,
        trial_ended=True
    )
    user = create_test_user(account=account)

    # new subscription data
    new_quantity = 11
    old_price = create_test_recurring_price(stripe_id=old_price_id)
    new_item = PurchaseItem(
        price=old_price,
        quantity=new_quantity,
        min_quantity=1
    )
    new_sub_mock = mocker.Mock()
    sub_modify_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'stripe.Subscription.modify',
        return_value=new_sub_mock
    )
    subscription_details_mock = mocker.Mock()
    get_subscription_details_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService.get_subscription_details',
        return_value=subscription_details_mock
    )

    invoice_item_price_stripe_id = 'pr_iwdasd'
    invoice_item_mock = mocker.Mock()
    invoice_item_mock.quantity = 1
    invoice_item_mock.price = mocker.Mock(
        stripe_id=invoice_item_price_stripe_id
    )
    invoice_items = [invoice_item_mock]

    service = StripeService(user=user)
    service.subscription_service = mocker.Mock(create=mocker.Mock())

    # act
    service._update_subscription(
        item=new_item,
        invoice_items=invoice_items
    )

    # assert
    sub_modify_mock.assert_called_once_with(
        id=old_subs_mock.id,
        items=[
            {
                "id": old_item_mock.id,
                "quantity": new_item.quantity,
            }
        ],
        add_invoice_items=[
            {
                "price": invoice_item_price_stripe_id,
                "quantity": 1,
            }
        ],
        trial_end='now',
        metadata={'account_id': account.id},
        description='Main'
    )
    get_subscription_details_mock.assert_called_once_with(new_sub_mock)
    service.subscription_service.update.assert_called_once_with(
        details=subscription_details_mock,
    )


def test_update_subscription__new_price__ok(mocker):

    # arrange

    # mock init
    customer_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
        return_value=customer_mock
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    # old subscription data
    old_price_id = 'price_old1213ad'
    old_sub_price_mock = mocker.Mock(id=old_price_id, currency='usd')
    old_item_mock = mocker.MagicMock(
        id=old_price_id,
        price=old_sub_price_mock
    )
    old_sub_data = {'items': mocker.Mock(data=[old_item_mock])}
    sub_id = 'sub_123AD'
    old_subs_mock = mocker.MagicMock(id=sub_id)
    old_subs_mock.__getitem__.side_effect = old_sub_data.__getitem__
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=old_subs_mock
    )

    customer_stripe_id = "cus_testNx9XuHa4xteob3"
    account = create_test_account(
        stripe_id=customer_stripe_id,
        trial_ended=True
    )
    user = create_test_user(account=account)

    # new subscription data
    new_price_id = 'price_new123'
    new_price = create_test_recurring_price(
        stripe_id=new_price_id,
        currency='usd'
    )
    new_quantity = 12
    new_item = PurchaseItem(
        price=new_price,
        quantity=new_quantity,
        min_quantity=11
    )
    new_sub_mock = mocker.Mock()
    sub_modify_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'stripe.Subscription.modify',
        return_value=new_sub_mock
    )
    subscription_details_mock = mocker.Mock()
    get_subscription_details_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService.get_subscription_details',
        return_value=subscription_details_mock
    )
    service = StripeService(user=user)
    service.subscription_service = mocker.Mock(create=mocker.Mock())

    # act
    service._update_subscription(
        item=new_item,
        invoice_items=[]
    )

    # assert
    sub_modify_mock.assert_called_once_with(
        id=old_subs_mock.id,
        items=[
            {
                "id": old_item_mock.id,
                "deleted": True,
            },
            {
                "price": new_price_id,
                "quantity": new_item.quantity,
            }
        ],
        add_invoice_items=[],
        trial_end='now',
        metadata={'account_id': account.id},
        description='Main'
    )
    get_subscription_details_mock.assert_called_once_with(new_sub_mock)
    service.subscription_service.update.assert_called_once_with(
        details=subscription_details_mock,
    )


def test_update_subscription__tenant_subscription__ok(mocker):

    # arrange
    # mock init
    customer_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
        return_value=customer_mock
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )

    # old subscription data
    old_price_id = 'price_1213ad'
    old_sub_price_mock = mocker.Mock(id=old_price_id)
    old_item_mock = mocker.MagicMock(
        id=old_price_id,
        price=old_sub_price_mock
    )
    old_sub_data = {'items': mocker.Mock(data=[old_item_mock])}
    old_sub_id = 'sub_123AD'
    old_subs_mock = mocker.MagicMock(id=old_sub_id)
    old_subs_mock.__getitem__.side_effect = old_sub_data.__getitem__
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=old_subs_mock
    )

    customer_stripe_id = "cus_testNx9XuHa4xteob3"
    master_account = create_test_account(
        trial_ended=False,
        lease_level=LeaseLevel.STANDARD
    )
    user = create_test_user(account=master_account)
    tenant_name = 'some tenant name'
    tenant_account = create_test_account(
        stripe_id=customer_stripe_id,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account,
        name='tenant',
        tenant_name=tenant_name
    )

    # new subscription data
    new_quantity = 11
    old_price = create_test_recurring_price(stripe_id=old_price_id)
    new_item = PurchaseItem(
        price=old_price,
        quantity=new_quantity,
        min_quantity=1
    )
    new_sub_mock = mocker.Mock()
    sub_modify_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'stripe.Subscription.modify',
        return_value=new_sub_mock
    )
    subscription_details_mock = mocker.Mock()
    get_subscription_details_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService.get_subscription_details',
        return_value=subscription_details_mock
    )

    invoice_item_price_stripe_id = 'pr_iwdasd'
    invoice_item_mock = mocker.Mock()
    invoice_item_mock.quantity = 1
    invoice_item_mock.price = mocker.Mock(
        stripe_id=invoice_item_price_stripe_id
    )
    invoice_items = [invoice_item_mock]

    service = StripeService(
        user=user,
        subscription_account=tenant_account
    )
    service.subscription_service = mocker.Mock(create=mocker.Mock())

    # act
    service._update_subscription(
        item=new_item,
        invoice_items=invoice_items
    )

    # assert
    sub_modify_mock.assert_called_once_with(
        id=old_subs_mock.id,
        items=[
            {
                "id": old_item_mock.id,
                "quantity": new_item.quantity,
            }
        ],
        add_invoice_items=[
            {
                "price": invoice_item_price_stripe_id,
                "quantity": 1,
            }
        ],
        trial_end='now',
        metadata={'account_id': tenant_account.id},
        description=tenant_name
    )
    get_subscription_details_mock.assert_called_once_with(new_sub_mock)
    service.subscription_service.update.assert_called_once_with(
        details=subscription_details_mock,
    )


def test_create_invoice__ok(mocker):

    # arrange
    # mock init
    customer_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
        return_value=customer_mock
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription'
    )
    # end mock init

    account = create_test_account()
    user = create_test_user(account=account)

    invoice_mock = mocker.Mock()
    invoice_create_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'stripe.Invoice.create',
        return_value=invoice_mock
    )
    invoice_item_create_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'stripe.InvoiceItem.create'
    )
    product = create_test_product(
        code='some code',
        stripe_id='product_123'
    )
    invoice_item_1 = PurchaseItem(
        price=create_test_recurring_price(product=product),
        quantity=1,
        min_quantity=1
    )
    invoice_item_2 = PurchaseItem(
        price=create_test_invoice_price(),
        quantity=2,
        min_quantity=1
    )
    service = StripeService(user=user)

    # act
    service._create_invoice(invoice_items=[invoice_item_1, invoice_item_2])

    # assert
    invoice_create_mock.assert_called_once_with(
        customer=customer_mock,
        collection_method='charge_automatically'
    )
    assert invoice_item_create_mock.call_count == 2
    invoice_item_create_mock.has_calls([
        mocker.call(
            invoice=invoice_mock,
            customer=customer_mock,
            price=invoice_item_1.price.stripe_id,
            quantity=invoice_item_1.quantity
        ),
        mocker.call(
            invoice=invoice_mock,
            customer=customer_mock,
            price=invoice_item_2.price.stripe_id,
            quantity=invoice_item_2.quantity
        )
    ])
    invoice_mock.finalize_invoice.assert_called_once()
    invoice_mock.pay.assert_called_once()


def test_create_invoice__invoice_is_already_paid__ok(mocker):

    # arrange
    # mock init
    customer_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
        return_value=customer_mock
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription'
    )
    # end mock init

    account = create_test_account()
    user = create_test_user(account=account)

    invoice_mock = mocker.Mock()
    invoice_create_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'stripe.Invoice.create',
        return_value=invoice_mock
    )
    invoice_mock.pay.side_effect = stripe.error.InvalidRequestError(
        message='Invoice is already paid',
        param=('some param',)
    )
    invoice_item_create_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'stripe.InvoiceItem.create'
    )
    product = create_test_product(
        code='some code',
        stripe_id='product_123'
    )
    invoice_item_1 = PurchaseItem(
        price=create_test_recurring_price(product=product),
        quantity=1,
        min_quantity=1
    )
    service = StripeService(user=user)

    # act
    service._create_invoice(invoice_items=[invoice_item_1])

    # assert
    invoice_create_mock.assert_called_once_with(
        customer=customer_mock,
        collection_method='charge_automatically'
    )
    invoice_item_create_mock.assert_called_once_with(
        invoice=invoice_mock,
        customer=customer_mock,
        price=invoice_item_1.price.stripe_id,
        quantity=invoice_item_1.quantity
    )
    invoice_mock.finalize_invoice.assert_called_once()
    invoice_mock.pay.assert_called_once()


def test_create_invoice__invoice_request_error__raise_exception(mocker):

    # arrange
    # mock init
    customer_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
        return_value=customer_mock
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription'
    )
    # end mock init

    account = create_test_account()
    user = create_test_user(account=account)

    invoice_mock = mocker.Mock()
    invoice_create_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'stripe.Invoice.create',
        return_value=invoice_mock
    )
    error_message = 'Some invoice request error'
    invoice_mock.pay.side_effect = stripe.error.InvalidRequestError(
        message=error_message,
        param=('some param',)
    )
    invoice_item_create_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'stripe.InvoiceItem.create'
    )
    product = create_test_product(
        code='some code',
        stripe_id='product_123'
    )
    invoice_item_1 = PurchaseItem(
        price=create_test_recurring_price(product=product),
        quantity=1,
        min_quantity=1
    )
    service = StripeService(user=user)

    # act
    with pytest.raises(stripe.error.InvalidRequestError) as ex:
        service._create_invoice(invoice_items=[invoice_item_1])

    # assert
    assert ex.value.user_message == error_message
    invoice_create_mock.assert_called_once_with(
        customer=customer_mock,
        collection_method='charge_automatically'
    )
    invoice_item_create_mock.assert_called_once_with(
        invoice=invoice_mock,
        customer=customer_mock,
        price=invoice_item_1.price.stripe_id,
        quantity=invoice_item_1.quantity
    )
    invoice_mock.finalize_invoice.assert_called_once()
    invoice_mock.pay.assert_called_once()


def test_off_session_purchase__create_subscription__ok(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=None
    )
    # end mock init

    account = create_test_account()
    user = create_test_user(account=account)
    subscription_item_mock = mocker.Mock()
    get_valid_subscription_item_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_valid_subscription_item',
        return_value=subscription_item_mock
    )
    invoice_items_mock = mocker.Mock()
    get_valid_invoice_items_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_valid_invoice_items',
        return_value=invoice_items_mock
    )
    service = StripeService(user=user)
    products_mock = mocker.Mock()
    create_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._create_subscription'
    )
    update_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._update_subscription'
    )
    create_invoice_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._create_invoice'
    )

    # act
    service._off_session_purchase(products=products_mock)

    # assert
    get_valid_subscription_item_mock.assert_called_once_with(products_mock)
    get_valid_invoice_items_mock.assert_called_once_with(products_mock)
    update_subscription_mock.assert_not_called()
    create_subscription_mock.assert_called_once_with(
        item=subscription_item_mock,
        invoice_items=invoice_items_mock
    )
    create_invoice_mock.assert_not_called()


def test_off_session_purchase_update_subscription__ok(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    subscription_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=subscription_mock
    )
    # end mock init

    account = create_test_account()
    user = create_test_user(account=account)
    subscription_item_mock = mocker.Mock()
    get_valid_subscription_item_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_valid_subscription_item',
        return_value=subscription_item_mock
    )
    invoice_items_mock = mocker.Mock()
    get_valid_invoice_items_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_valid_invoice_items',
        return_value=invoice_items_mock
    )
    service = StripeService(user=user)
    products_mock = mocker.Mock()
    create_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._create_subscription'
    )
    update_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._update_subscription'
    )
    create_invoice_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._create_invoice'
    )

    # act
    service._off_session_purchase(products=products_mock)

    # assert
    get_valid_subscription_item_mock.assert_called_once_with(products_mock)
    get_valid_invoice_items_mock.assert_called_once_with(products_mock)
    update_subscription_mock.assert_called_once_with(
        item=subscription_item_mock,
        invoice_items=invoice_items_mock
    )
    create_subscription_mock.assert_not_called()
    create_invoice_mock.assert_not_called()


def test_off_session_purchase__invoice_items__ok(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=None
    )
    # end mock init

    account = create_test_account()
    user = create_test_user(account=account)
    get_valid_subscription_item_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_valid_subscription_item',
        return_value=None
    )
    invoice_items_mock = mocker.Mock()
    get_valid_invoice_items_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_valid_invoice_items',
        return_value=invoice_items_mock
    )
    service = StripeService(user=user)
    products_mock = mocker.Mock()
    create_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._create_subscription'
    )
    update_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._update_subscription'
    )
    create_invoice_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._create_invoice'
    )

    # act
    service._off_session_purchase(products=products_mock)

    # assert
    get_valid_subscription_item_mock.assert_called_once_with(products_mock)
    get_valid_invoice_items_mock.assert_called_once_with(products_mock)
    update_subscription_mock.assert_not_called()
    create_subscription_mock.assert_not_called()
    create_invoice_mock.assert_called_once_with(invoice_items_mock)


def test_get_subscription_checkout_link__not_trial__ok(mocker):

    # arrange
    # mock init
    customer_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
        return_value=customer_mock
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=None
    )
    # end mock init

    account = create_test_account(trial_ended=False)
    user = create_test_user(account=account)

    product_code = 'my_premium'
    sub_price_stripe_id = 'pr_12DSADasd'
    sub_item_quantity = 10
    sub_price_code = 'pneumatic_monthly'
    sub_item = mocker.Mock(quantity=sub_item_quantity)
    sub_item.price = mocker.Mock(
        trial_days=None,
        stripe_id=sub_price_stripe_id,
        code=sub_price_code,
        product=mocker.Mock(code=product_code)
    )
    invoice_item_1 = mocker.Mock(quantity=1)
    invoice_item_1.price = mocker.Mock(stripe_id='price_item_1awd')

    invoice_item_2 = mocker.Mock(quantity=2)
    invoice_item_2.price = mocker.Mock(stripe_id='price_item_2zxc')

    invoice_items = [invoice_item_1, invoice_item_2]
    cancel_url = 'http://pneumatic.com/some-cancel'
    success_url = 'http://pneumatic.com/some-success'
    success_url_with_token = 'http://pneumatic.com/some-success?token=123'

    get_success_url_with_token_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_success_url_with_token',
        return_value=success_url_with_token
    )
    checkout_link = 'http://stripe.com/some-link'
    get_checkout_session_url_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_checkout_session_url',
        return_value=checkout_link
    )
    service = StripeService(user=user)

    # act
    result = service._get_subscription_checkout_link(
        item=sub_item,
        success_url=success_url,
        cancel_url=cancel_url,
        invoice_items=invoice_items
    )

    # assert
    assert result == checkout_link
    get_success_url_with_token_mock.assert_called_once_with(
        url=success_url,
        subscription_data=TokenSubscriptionData(
            billing_plan=product_code,
            max_users=sub_item_quantity,
            trial_days=None
        )
    )
    get_checkout_session_url_mock.assert_called_once_with(
        line_items=[
            {
                "price": sub_price_stripe_id,
                "quantity": sub_item_quantity
            },
            {
                "price": invoice_item_1.price.stripe_id,
                "quantity": invoice_item_1.quantity
            },
            {
                "price": invoice_item_2.price.stripe_id,
                "quantity": invoice_item_2.quantity
            }
        ],
        success_url=success_url_with_token,
        cancel_url=cancel_url,
        mode='subscription',
        allow_promotion_codes=True,
        subscription_data={
            'metadata': {'account_id': account.id},
            'description': 'Main',
        }
    )


def test_get_subscription_checkout_link__with_trial__ok(mocker):

    # arrange
    # mock init
    customer_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
        return_value=customer_mock
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=None
    )
    # end mock init

    account = create_test_account(trial_ended=False)
    user = create_test_user(account=account)

    product_code = 'my_premium'
    sub_price_stripe_id = 'pr_12DSADasd'
    sub_item_quantity = 10
    sub_price_code = 'pneumatic_monthly'
    sub_trial_days = 14
    sub_item = mocker.Mock(quantity=sub_item_quantity)
    sub_item.price = mocker.Mock(
        trial_days=sub_trial_days,
        stripe_id=sub_price_stripe_id,
        code=sub_price_code,
        product=mocker.Mock(code=product_code)
    )
    invoice_item_1 = mocker.Mock(quantity=1)
    invoice_item_1.price = mocker.Mock(stripe_id='price_item_1awd')

    invoice_item_2 = mocker.Mock(quantity=2)
    invoice_item_2.price = mocker.Mock(stripe_id='price_item_2zxc')

    invoice_items = [invoice_item_1, invoice_item_2]
    cancel_url = 'http://pneumatic.com/some-cancel'
    success_url = 'http://pneumatic.com/some-success'
    success_url_with_token = 'http://pneumatic.com/some-success?token=123'

    get_success_url_with_token_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_success_url_with_token',
        return_value=success_url_with_token
    )
    checkout_link = 'http://stripe.com/some-link'
    get_checkout_session_url_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_checkout_session_url',
        return_value=checkout_link
    )
    service = StripeService(user=user)

    # act
    result = service._get_subscription_checkout_link(
        item=sub_item,
        success_url=success_url,
        cancel_url=cancel_url,
        invoice_items=invoice_items
    )

    # assert
    assert result == checkout_link
    get_success_url_with_token_mock.assert_called_once_with(
        url=success_url,
        subscription_data=TokenSubscriptionData(
            billing_plan=product_code,
            max_users=sub_item_quantity,
            trial_days=sub_trial_days
        )
    )
    get_checkout_session_url_mock.assert_called_once_with(
        line_items=[
            {
                "price": sub_price_stripe_id,
                "quantity": sub_item_quantity
            },
            {
                "price": invoice_item_1.price.stripe_id,
                "quantity": invoice_item_1.quantity
            },
            {
                "price": invoice_item_2.price.stripe_id,
                "quantity": invoice_item_2.quantity
            }
        ],
        success_url=success_url_with_token,
        cancel_url=cancel_url,
        mode='subscription',
        allow_promotion_codes=True,
        subscription_data={
            "trial_period_days": sub_trial_days,
            'metadata': {'account_id': account.id},
            'description': 'Main',
        }
    )


def test_get_subscription_checkout_link__trial_ended__not_start_trial(mocker):

    # arrange
    # mock init
    customer_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
        return_value=customer_mock
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=None
    )
    # end mock init

    account = create_test_account(trial_ended=True)
    user = create_test_user(account=account)

    product_code = 'my_premium'
    sub_price_stripe_id = 'pr_12DSADasd'
    sub_item_quantity = 10
    sub_price_code = 'pneumatic_monthly'
    sub_trial_days = 14
    sub_item = mocker.Mock(quantity=sub_item_quantity)
    sub_item.price = mocker.Mock(
        trial_days=sub_trial_days,
        stripe_id=sub_price_stripe_id,
        code=sub_price_code,
        product=mocker.Mock(code=product_code)
    )
    invoice_item_1 = mocker.Mock(quantity=1)
    invoice_item_1.price = mocker.Mock(stripe_id='price_item_1awd')

    invoice_item_2 = mocker.Mock(quantity=2)
    invoice_item_2.price = mocker.Mock(stripe_id='price_item_2zxc')

    invoice_items = [invoice_item_1, invoice_item_2]
    cancel_url = 'http://pneumatic.com/some-cancel'
    success_url = 'http://pneumatic.com/some-success'
    success_url_with_token = 'http://pneumatic.com/some-success?token=123'

    get_success_url_with_token_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_success_url_with_token',
        return_value=success_url_with_token
    )
    checkout_link = 'http://stripe.com/some-link'
    get_checkout_session_url_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_checkout_session_url',
        return_value=checkout_link
    )
    service = StripeService(user=user)

    # act
    result = service._get_subscription_checkout_link(
        item=sub_item,
        success_url=success_url,
        cancel_url=cancel_url,
        invoice_items=invoice_items
    )

    # assert
    assert result == checkout_link
    get_success_url_with_token_mock.assert_called_once_with(
        url=success_url,
        subscription_data=TokenSubscriptionData(
            billing_plan=product_code,
            max_users=sub_item_quantity,
            trial_days=None
        )
    )
    get_checkout_session_url_mock.assert_called_once_with(
        line_items=[
            {
                "price": sub_price_stripe_id,
                "quantity": sub_item_quantity
            },
            {
                "price": invoice_item_1.price.stripe_id,
                "quantity": invoice_item_1.quantity
            },
            {
                "price": invoice_item_2.price.stripe_id,
                "quantity": invoice_item_2.quantity
            }
        ],
        success_url=success_url_with_token,
        cancel_url=cancel_url,
        mode='subscription',
        allow_promotion_codes=True,
        subscription_data={
            'metadata': {'account_id': account.id},
            'description': 'Main',
        }
    )


def test_get_subscription_checkout_link__tenant__ok(mocker):

    # arrange
    # mock init
    customer_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
        return_value=customer_mock
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=None
    )
    # end mock init

    master_account = create_test_account(trial_ended=True)
    user = create_test_user(account=master_account)
    tenant_name = 'Some Tenant name'
    tenant = create_test_account(
        lease_level=LeaseLevel.TENANT,
        master_account=master_account,
        tenant_name=tenant_name
    )
    create_test_user(
        account=tenant,
        email='tenant@owner.com'
    )

    product_code = 'my_premium'
    sub_price_stripe_id = 'pr_12DSADasd'
    sub_item_quantity = 10
    sub_price_code = 'pneumatic_monthly'
    sub_item = mocker.Mock(quantity=sub_item_quantity)
    sub_item.price = mocker.Mock(
        trial_days=None,
        stripe_id=sub_price_stripe_id,
        code=sub_price_code,
        product=mocker.Mock(code=product_code)
    )
    cancel_url = 'http://pneumatic.com/some-cancel'
    success_url = 'http://pneumatic.com/some-success'
    success_url_with_token = 'http://pneumatic.com/some-success?token=123'

    get_success_url_with_token_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_success_url_with_token',
        return_value=success_url_with_token
    )
    checkout_link = 'http://stripe.com/some-link'
    get_checkout_session_url_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_checkout_session_url',
        return_value=checkout_link
    )
    service = StripeService(
        user=user,
        subscription_account=tenant
    )

    # act
    result = service._get_subscription_checkout_link(
        item=sub_item,
        success_url=success_url,
        cancel_url=cancel_url,
    )

    # assert
    assert result == checkout_link
    get_success_url_with_token_mock.assert_called_once_with(
        url=success_url,
        subscription_data=TokenSubscriptionData(
            billing_plan=product_code,
            max_users=sub_item_quantity,
            trial_days=None
        )
    )
    get_checkout_session_url_mock.assert_called_once_with(
        line_items=[
            {
                "price": sub_price_stripe_id,
                "quantity": sub_item_quantity
            }
        ],
        success_url=success_url_with_token,
        cancel_url=cancel_url,
        mode='subscription',
        allow_promotion_codes=True,
        subscription_data={
            'metadata': {'account_id': tenant.id},
            'description': tenant_name,
        }
    )


def test_get_payment_checkout_link__ok(mocker):

    # arrange
    # mock init
    customer_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
        return_value=customer_mock
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=None
    )
    # end mock init

    account = create_test_account()
    user = create_test_user(account=account)

    invoice_item_1 = mocker.Mock(
        quantity=1,
        min_quantity=1
    )
    invoice_item_1.price = mocker.Mock(
        stripe_id='price_item_1awd',
        max_quantity=2
    )

    invoice_item_2 = mocker.Mock(
        quantity=10,
        min_quantity=5
    )
    invoice_item_2.price = mocker.Mock(
        stripe_id='price_item_2zxc',
        max_quantity=100
    )

    invoice_items = [invoice_item_1, invoice_item_2]
    cancel_url = 'http://pneumatic.com/some-cancel'
    success_url = 'http://pneumatic.com/some-success'
    success_url_with_token = 'http://pneumatic.com/some-success?token=123'

    get_success_url_with_token_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_success_url_with_token',
        return_value=success_url_with_token
    )
    checkout_link = 'http://stripe.com/some-link'
    get_checkout_session_url_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_checkout_session_url',
        return_value=checkout_link
    )
    service = StripeService(user=user)

    # act
    result = service._get_payment_checkout_link(
        success_url=success_url,
        cancel_url=cancel_url,
        invoice_items=invoice_items
    )

    # assert
    assert result == checkout_link
    get_success_url_with_token_mock.assert_called_once_with(url=success_url)
    get_checkout_session_url_mock.assert_called_once_with(
        line_items=[
            {
                "price": invoice_item_1.price.stripe_id,
                "quantity": invoice_item_1.quantity,
                "adjustable_quantity": {
                    'enabled': True,
                    'maximum': invoice_item_1.price.max_quantity,
                    'minimum': invoice_item_1.min_quantity
                }
            },
            {
                "price": invoice_item_2.price.stripe_id,
                "quantity": invoice_item_2.quantity,
                "adjustable_quantity": {
                    'enabled': True,
                    'maximum': invoice_item_2.price.max_quantity,
                    'minimum': invoice_item_2.min_quantity
                }
            }
        ],
        success_url=success_url_with_token,
        cancel_url=cancel_url,
        mode='payment',
        allow_promotion_codes=True,
    )


def test_get_payment_checkout_link__not_invoice_items__return_none(mocker):

    # arrange
    # mock init
    customer_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
        return_value=customer_mock
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=None
    )
    # end mock init

    account = create_test_account()
    user = create_test_user(account=account)

    invoice_items = []
    cancel_url = 'http://pneumatic.com/some-cancel'
    success_url = 'http://pneumatic.com/some-success'

    get_success_url_with_token_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_success_url_with_token'
    )
    get_checkout_session_url_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_checkout_session_url'
    )
    service = StripeService(user=user)

    # act
    result = service._get_payment_checkout_link(
        success_url=success_url,
        cancel_url=cancel_url,
        invoice_items=invoice_items
    )

    # assert
    assert result is None
    get_success_url_with_token_mock.assert_not_called()
    get_checkout_session_url_mock.assert_not_called()


def test_get_checkout_link__for_subscription__ok(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=None
    )
    # end mock init

    account = create_test_account()
    user = create_test_user(account=account)

    products = mocker.Mock()
    cancel_url = 'http://pneumatic.com/some-cancel'
    success_url = 'http://pneumatic.com/some-success'

    subscription_item_mock = mocker.Mock()
    get_valid_subscription_item_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_valid_subscription_item',
        return_value=subscription_item_mock
    )
    invoice_items_mock = mocker.Mock()
    get_valid_invoice_items_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_valid_invoice_items',
        return_value=invoice_items_mock
    )
    checkout_link = 'http://stripe.com/some-checkout'
    get_subscription_checkout_link_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_subscription_checkout_link',
        return_value=checkout_link
    )
    get_payment_checkout_link_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_payment_checkout_link'
    )
    service = StripeService(user=user)

    # act
    result = service._get_checkout_link(
        products=products,
        success_url=success_url,
        cancel_url=cancel_url,
    )

    # assert
    assert result == checkout_link
    get_valid_subscription_item_mock.assert_called_once_with(products)
    get_valid_invoice_items_mock.assert_called_once_with(products)
    get_subscription_checkout_link_mock.assert_called_once_with(
        item=subscription_item_mock,
        invoice_items=invoice_items_mock,
        success_url=success_url,
        cancel_url=cancel_url,
    )
    get_payment_checkout_link_mock.assert_not_called()


def test_get_checkout_link__for_invoice_items__ok(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=None
    )
    # end mock init

    account = create_test_account()
    user = create_test_user(account=account)

    products = mocker.Mock()
    cancel_url = 'http://pneumatic.com/some-cancel'
    success_url = 'http://pneumatic.com/some-success'

    get_valid_subscription_item_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_valid_subscription_item',
        return_value=None
    )
    invoice_items_mock = mocker.Mock()
    get_valid_invoice_items_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_valid_invoice_items',
        return_value=invoice_items_mock
    )
    get_subscription_checkout_link_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_subscription_checkout_link'
    )
    checkout_link = 'http://stripe.com/some-checkout'
    get_payment_checkout_link_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_payment_checkout_link',
        return_value=checkout_link
    )
    service = StripeService(user=user)

    # act
    result = service._get_checkout_link(
        products=products,
        success_url=success_url,
        cancel_url=cancel_url,
    )

    # assert
    assert result == checkout_link
    get_valid_subscription_item_mock.assert_called_once_with(products)
    get_valid_invoice_items_mock.assert_called_once_with(products)
    get_subscription_checkout_link_mock.assert_not_called()
    get_payment_checkout_link_mock.assert_called_once_with(
        invoice_items=invoice_items_mock,
        success_url=success_url,
        cancel_url=cancel_url,
    )


def test_get_checkout_link__not_valid_products__return_none(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=None
    )
    # end mock init

    account = create_test_account()
    user = create_test_user(account=account)

    products = mocker.Mock()
    cancel_url = 'http://pneumatic.com/some-cancel'
    success_url = 'http://pneumatic.com/some-success'

    get_valid_subscription_item_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_valid_subscription_item',
        return_value=None
    )
    get_valid_invoice_items_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_valid_invoice_items',
        return_value=None
    )
    get_subscription_checkout_link_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_subscription_checkout_link'
    )
    get_payment_checkout_link_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_payment_checkout_link',
    )
    service = StripeService(user=user)

    # act
    result = service._get_checkout_link(
        products=products,
        success_url=success_url,
        cancel_url=cancel_url,
    )

    # assert
    assert result is None
    get_valid_subscription_item_mock.assert_called_once_with(products)
    get_valid_invoice_items_mock.assert_called_once_with(products)
    get_subscription_checkout_link_mock.assert_not_called()
    get_payment_checkout_link_mock.assert_not_called()


def test_get_valid_premium_subscription_item__ok(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    subscription_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=subscription_mock
    )
    # end mock init
    account = create_test_account(
        max_users=6
    )
    user = create_test_user(account=account)
    price = create_test_recurring_price(
        min_quantity=5,
        max_quantity=999999
    )
    service = StripeService(user=user)
    quantity = 7

    # act
    result = service._get_valid_premium_subscription_item(
        price=price,
        quantity=quantity
    )

    # assert
    assert isinstance(result, PurchaseItem)
    assert result.price == price
    assert result.quantity == quantity
    assert result.min_quantity is None


def test_get_valid_premium_subscription_item__decrease_subscription__raise(
    mocker
):

    """ Decrease less than account.max_users """

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    subscription_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=subscription_mock
    )
    # end mock init
    account = create_test_account(
        max_users=10,
        plan=BillingPlanType.PREMIUM
    )
    user = create_test_user(account=account)
    price = create_test_recurring_price(
        min_quantity=5,
        max_quantity=99999
    )
    service = StripeService(user=user)
    quantity = 9

    # act
    with pytest.raises(DecreaseSubscription) as ex:
        service._get_valid_premium_subscription_item(
            price=price,
            quantity=quantity
        )

    # assert
    assert ex.value.message == messages.MSG_BL_0004


def test_get_valid_premium_subscription_item__min_quantity_reached__raise(
    mocker
):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    subscription_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=subscription_mock
    )
    # end mock init
    account = create_test_account(
        max_users=1,
        plan=BillingPlanType.PREMIUM
    )
    user = create_test_user(account=account)
    price = create_test_recurring_price(
        min_quantity=3,
        max_quantity=999999
    )
    service = StripeService(user=user)
    quantity = 2

    # act
    with pytest.raises(SubsMinQuantityReached) as ex:
        service._get_valid_premium_subscription_item(
            price=price,
            quantity=quantity
        )

    # assert
    assert ex.value.message == messages.MSG_BL_0012(
        price.min_quantity,
        price.product.name
    )


def test_get_valid_premium_subscription_item__max_quantity_reached__raise(
    mocker
):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    subscription_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=subscription_mock
    )
    # end mock init
    account = create_test_account(max_users=1)
    user = create_test_user(account=account)
    price = create_test_recurring_price(
        min_quantity=2,
        max_quantity=5
    )
    service = StripeService(user=user)
    quantity = 6

    # act
    with pytest.raises(SubsMaxQuantityReached) as ex:
        service._get_valid_premium_subscription_item(
            price=price,
            quantity=quantity
        )

    # assert
    assert ex.value.message == messages.MSG_BL_0011(
        price.max_quantity,
        price.product.name
    )


def test_get_valid_premium_subscription_item__current_fractionalcoo__ok(
    mocker
):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    subscription_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=subscription_mock
    )
    # end mock init
    account = create_test_account(
        plan=BillingPlanType.FRACTIONALCOO,
        max_users=99999
    )
    user = create_test_user(account=account)
    price = create_test_recurring_price(
        min_quantity=5,
        max_quantity=999999
    )
    service = StripeService(user=user)
    quantity = 5

    # act
    result = service._get_valid_premium_subscription_item(
        price=price,
        quantity=quantity
    )

    # assert
    assert isinstance(result, PurchaseItem)
    assert result.price == price
    assert result.quantity == quantity
    assert result.min_quantity is None


def test_get_valid_fractionalcoo_subscription_item__ok(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    subscription_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=subscription_mock
    )
    # end mock init
    account = create_test_account(
        max_users=5
    )
    user = create_test_user(account=account)
    price = create_test_recurring_price(
        max_quantity=1,
        min_quantity=0
    )
    service = StripeService(user=user)
    quantity = 1

    # act
    result = service._get_valid_fractionalcoo_subscription_item(
        price=price,
        quantity=quantity
    )

    # assert
    assert isinstance(result, PurchaseItem)
    assert result.price == price
    assert result.quantity == quantity
    assert result.min_quantity is None


def test_get_valid_unlimited_subscription_item__ok(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    subscription_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=subscription_mock
    )
    # end mock init
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    create_test_account(master_account=account, lease_level=LeaseLevel.TENANT)
    user = create_test_user(account=account)
    price = create_test_recurring_price(
        max_quantity=2,
        min_quantity=0
    )
    service = StripeService(user=user)
    quantity = 1

    # act
    result = service._get_valid_unlimited_subscription_item(
        price=price,
        quantity=quantity
    )

    # assert
    assert isinstance(result, PurchaseItem)
    assert result.price == price
    assert result.quantity == 1
    assert result.min_quantity is None


def test_get_valid_fractionalcoo_subscription_item__min_quantity_reached__r(
    mocker
):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    subscription_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=subscription_mock
    )
    # end mock init
    account = create_test_account(max_users=1)
    user = create_test_user(account=account)
    price = create_test_recurring_price(
        min_quantity=0,
        max_quantity=1
    )
    service = StripeService(user=user)
    quantity = -1

    # act
    with pytest.raises(SubsMinQuantityReached) as ex:
        service._get_valid_fractionalcoo_subscription_item(
            price=price,
            quantity=quantity
        )

    # assert
    assert ex.value.message == messages.MSG_BL_0012(
        price.min_quantity,
        price.product.name
    )


def test_get_valid_fractionalcoo_subscription_item__max_quantity_reached__r(
    mocker
):

    """ Decrease less than account.max_users """

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    subscription_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=subscription_mock
    )
    # end mock init
    account = create_test_account(max_users=1)
    user = create_test_user(account=account)
    price = create_test_recurring_price(
        min_quantity=0,
        max_quantity=1
    )
    service = StripeService(user=user)
    quantity = 2

    # act
    with pytest.raises(SubsMaxQuantityReached) as ex:
        service._get_valid_fractionalcoo_subscription_item(
            price=price,
            quantity=quantity
        )

    # assert
    assert ex.value.message == messages.MSG_BL_0011(
        price.max_quantity,
        price.product.name
    )


def test_get_valid_subscription_item__update_subs__ok(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    # old subscription data
    product = create_test_product(code=BillingPlanType.PREMIUM)
    price_code = 'pneumatic_monthly'
    price = create_test_recurring_price(
        code=price_code,
        product=product
    )
    old_sub_price_mock = mocker.Mock(
        currency='usd',
        id=price.stripe_id
    )
    old_item_mock = mocker.MagicMock(price=old_sub_price_mock)
    old_sub_data = {'items': mocker.Mock(data=[old_item_mock])}
    old_subs_mock = mocker.MagicMock()
    old_subs_mock.__getitem__.side_effect = old_sub_data.__getitem__
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=old_subs_mock
    )
    # end mock init
    account_max_users = 9
    account = create_test_account(max_users=account_max_users)
    user = create_test_user(account=account)
    product_quantity = 10
    products = [
        {
            'code': price_code,
            'quantity': product_quantity,
        }
    ]
    subscription_item_mock = mocker.Mock()
    get_valid_premium_subscription_item_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_valid_premium_subscription_item',
        return_value=subscription_item_mock
    )
    service = StripeService(user=user)

    # act
    result = service._get_valid_subscription_item(
        products=products
    )

    # assert
    assert result == subscription_item_mock
    get_valid_premium_subscription_item_mock.assert_called_once_with(
        price=price,
        quantity=product_quantity
    )


def test_get_valid_subscription_item__create_archived_price__raise_exception(
    mocker
):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=None
    )
    # end mock init
    account_max_users = 9
    account = create_test_account(max_users=account_max_users)
    user = create_test_user(account=account)
    price_code = 'pneumatic_monthly'
    product_quantity = 10
    products = [
        {
            'code': price_code,
            'quantity': product_quantity,
        }
    ]
    product = create_test_product(code=BillingPlanType.PREMIUM)
    create_test_recurring_price(
        code=price_code,
        product=product,
        status=PriceStatus.ARCHIVED
    )
    subscription_item_mock = mocker.Mock()
    get_valid_premium_subscription_item_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_valid_premium_subscription_item',
        return_value=subscription_item_mock
    )
    service = StripeService(user=user)

    # act
    with pytest.raises(PurchaseArchivedPrice) as ex:
        service._get_valid_subscription_item(
            products=products
        )

    # assert
    assert ex.value.message == messages.MSG_BL_0016
    get_valid_premium_subscription_item_mock.assert_not_called()


def test_get_valid_subscription_item__update_to_archived_price__raise_ex(
    mocker
):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    price_stripe_id = 'price_123'
    price_mock = mocker.Mock(id=price_stripe_id)
    item_mock = mocker.MagicMock(price=price_mock)
    subscription_mock = {
        'items': mocker.Mock(data=[item_mock]),
    }
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=subscription_mock
    )
    product = create_test_product(code=BillingPlanType.PREMIUM)
    create_test_recurring_price(
        stripe_id=price_stripe_id,
        status=PriceStatus.ACTIVE,
        currency='usd',
        product=product
    )
    # end mock init
    account_max_users = 9
    account = create_test_account(max_users=account_max_users)
    user = create_test_user(account=account)
    new_price_code = 'pneumatic_monthly'
    product_quantity = 10
    products = [
        {
            'code': new_price_code,
            'quantity': product_quantity,
        }
    ]
    create_test_recurring_price(
        code=new_price_code,
        status=PriceStatus.ARCHIVED,
        product=product
    )
    get_valid_premium_subscription_item_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_valid_premium_subscription_item',
    )
    service = StripeService(user=user)

    # act
    with pytest.raises(PurchaseArchivedPrice) as ex:
        service._get_valid_subscription_item(
            products=products
        )

    # assert
    assert ex.value.message == messages.MSG_BL_0016
    get_valid_premium_subscription_item_mock.assert_not_called()


def test_get_valid_subscription_item__update_archived_price__ok(
    mocker
):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    price_stripe_id = 'price_123'
    price_mock = mocker.Mock(id=price_stripe_id)
    item_mock = mocker.MagicMock(price=price_mock)
    subscription_mock = {
        'items': mocker.Mock(data=[item_mock]),
    }
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=subscription_mock
    )
    current_price = create_test_recurring_price(
        stripe_id=price_stripe_id,
        status=PriceStatus.ARCHIVED,
        currency='usd'
    )
    # end mock init
    account_max_users = 9
    account = create_test_account(max_users=account_max_users)
    user = create_test_user(account=account)
    product_quantity = 10
    products = [
        {
            'code': current_price.code,
            'quantity': product_quantity,
        }
    ]
    subscription_item_mock = mocker.Mock()
    get_valid_premium_subscription_item_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_valid_premium_subscription_item',
        return_value=subscription_item_mock
    )
    service = StripeService(user=user)

    # act
    result = service._get_valid_subscription_item(
        products=products
    )

    # assert
    assert result == subscription_item_mock
    get_valid_premium_subscription_item_mock.assert_called_once_with(
        price=current_price,
        quantity=product_quantity
    )


def test_get_valid_subscription_item__price_not_exist__skip(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    subscription_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=subscription_mock
    )
    # end mock init
    account = create_test_account()
    user = create_test_user(account=account)
    price_code = 'pneumatic_monthly'
    products = [
        {
            'code': price_code,
            'quantity': 10,
        }
    ]
    create_test_invoice_price(code=price_code)
    service = StripeService(user=user)

    # act
    result = service._get_valid_subscription_item(
        products=products
    )

    # assert
    assert result is None


def test_get_valid_subscription_item__price_inactive__skip(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    subscription_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=subscription_mock
    )
    # end mock init
    account = create_test_account()
    user = create_test_user(account=account)
    price_code = 'pneumatic_monthly'
    products = [
        {
            'code': price_code,
            'quantity': 10,
        }
    ]
    create_test_recurring_price(
        code=price_code,
        status=PriceStatus.INACTIVE
    )
    service = StripeService(user=user)

    # act
    result = service._get_valid_subscription_item(
        products=products
    )

    # assert
    assert result is None


def test_get_valid_subscription_item__multiple_subs__raise_exception(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    subscription_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=subscription_mock
    )
    # end mock init
    account_max_users = 9
    account = create_test_account(max_users=account_max_users)
    user = create_test_user(account=account)
    price_code_1 = 'pneumatic_monthly'
    price_code_2 = 'pneumatic_annual'
    products = [
        {
            'code': price_code_1,
            'quantity': 10,
        },
        {
            'code': price_code_2,
            'quantity': 12,
        }
    ]
    create_test_recurring_price(code=price_code_1)
    product = create_test_product(
        stripe_id='prod_132',
        code='some code',
    )
    create_test_recurring_price(
        code=price_code_2,
        stripe_id='price_123',
        product=product
    )
    service = StripeService(user=user)

    # act
    with pytest.raises(MultipleSubscriptionsNotAllowed) as ex:
        service._get_valid_subscription_item(
            products=products
        )

    # assert
    assert ex.value.message == messages.MSG_BL_0006


def test_get_valid_subscription_item__change_currency__raise_exception(
    mocker
):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    # old subscription data
    product = create_test_product()
    current_price_stripe_id = 'price_123asd'
    create_test_recurring_price(
        code='some_code',
        product=product,
        stripe_id=current_price_stripe_id
    )
    old_sub_price_mock = mocker.Mock(
        id=current_price_stripe_id,
        currency='usd'
    )
    old_item_mock = mocker.MagicMock(price=old_sub_price_mock)
    old_sub_data = {'items': mocker.Mock(data=[old_item_mock])}
    old_subs_mock = mocker.MagicMock()
    old_subs_mock.__getitem__.side_effect = old_sub_data.__getitem__
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=old_subs_mock
    )

    # end mock init
    account = create_test_account(max_users=1)
    user = create_test_user(account=account)
    price_code = 'premium_monthly'
    product_quantity = 2
    products = [
        {
            'code': price_code,
            'quantity': product_quantity,
        }
    ]
    create_test_recurring_price(
        code=price_code,
        max_quantity=2,
        currency='eur',
        product=product
    )
    service = StripeService(user=user)

    # act
    with pytest.raises(ChangeCurrencyDisallowed) as ex:
        service._get_valid_subscription_item(
            products=products
        )

    # assert
    assert ex.value.message == messages.MSG_BL_0010


def test_get_valid_subscription_item__undefined_plan__raise(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    # old subscription data
    price_code = 'some_price'
    product = create_test_product(code='undefined')
    current_price = create_test_recurring_price(
        code=price_code,
        product=product
    )
    old_sub_price_mock = mocker.Mock(
        id=current_price.stripe_id,
        currency='usd'
    )
    old_item_mock = mocker.MagicMock(price=old_sub_price_mock)
    old_sub_data = {'items': mocker.Mock(data=[old_item_mock])}
    old_subs_mock = mocker.MagicMock()
    old_subs_mock.__getitem__.side_effect = old_sub_data.__getitem__
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=old_subs_mock
    )
    # end mock init
    account_max_users = 9
    account = create_test_account(max_users=account_max_users)
    user = create_test_user(account=account)
    product_quantity = 10
    products = [
        {
            'code': price_code,
            'quantity': product_quantity,
        }
    ]
    service = StripeService(user=user)

    # act
    with pytest.raises(UnsupportedPlan) as ex:
        service._get_valid_subscription_item(
            products=products
        )

    # assert
    assert ex.value.message == messages.MSG_BL_0015


def test_get_valid_invoice_items__ok(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    # old subscription data
    old_sub_price_mock = mocker.Mock(currency='usd')
    old_item_mock = mocker.MagicMock(price=old_sub_price_mock)
    old_sub_data = {'items': mocker.Mock(data=[old_item_mock])}
    old_subs_mock = mocker.MagicMock()
    old_subs_mock.__getitem__.side_effect = old_sub_data.__getitem__
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=old_subs_mock
    )
    # end mock init
    user = create_test_user()
    price_code = 'setup_addon'
    product_quantity = 2
    products = [
        {
            'code': price_code,
            'quantity': product_quantity,
        }
    ]
    price = create_test_invoice_price(
        code=price_code,
        min_quantity=2,
        max_quantity=3,
    )
    service = StripeService(user=user)

    # act
    result = service._get_valid_invoice_items(
        products=products
    )

    # assert
    assert len(result) == 1
    assert isinstance(result[0], PurchaseItem)
    assert result[0].price == price
    assert result[0].quantity == product_quantity
    assert result[0].min_quantity == price.min_quantity


def test_get_valid_invoice_items__product_not_exist__skip(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    # old subscription data
    old_sub_price_mock = mocker.Mock(currency='usd')
    old_item_mock = mocker.MagicMock(price=old_sub_price_mock)
    old_sub_data = {'items': mocker.Mock(data=[old_item_mock])}
    old_subs_mock = mocker.MagicMock()
    old_subs_mock.__getitem__.side_effect = old_sub_data.__getitem__
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=old_subs_mock
    )
    # end mock init
    user = create_test_user()
    price_code = 'setup_addon'
    product_quantity = 1
    products = [
        {
            'code': price_code,
            'quantity': product_quantity,
        }
    ]
    create_test_recurring_price(code=price_code)
    service = StripeService(user=user)

    # act
    result = service._get_valid_invoice_items(
        products=products
    )

    # assert
    assert len(result) == 0


def test_get_valid_invoice_items__price_inactive__skip(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    # old subscription data
    old_sub_price_mock = mocker.Mock(currency='usd')
    old_item_mock = mocker.MagicMock(price=old_sub_price_mock)
    old_sub_data = {'items': mocker.Mock(data=[old_item_mock])}
    old_subs_mock = mocker.MagicMock()
    old_subs_mock.__getitem__.side_effect = old_sub_data.__getitem__
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=old_subs_mock
    )
    # end mock init
    user = create_test_user()
    price_code = 'setup_addon'
    product_quantity = 1
    products = [
        {
            'code': price_code,
            'quantity': product_quantity,
        }
    ]
    create_test_invoice_price(
        code=price_code,
        status=PriceStatus.INACTIVE
    )
    service = StripeService(user=user)

    # act
    result = service._get_valid_invoice_items(
        products=products
    )

    # assert
    assert len(result) == 0


def test_get_valid_invoice_items__max_quantity_reached__raise_exception(
    mocker
):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    # old subscription data
    old_sub_price_mock = mocker.Mock(currency='usd')
    old_item_mock = mocker.MagicMock(price=old_sub_price_mock)
    old_sub_data = {'items': mocker.Mock(data=[old_item_mock])}
    old_subs_mock = mocker.MagicMock()
    old_subs_mock.__getitem__.side_effect = old_sub_data.__getitem__
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=old_subs_mock
    )
    # end mock init
    user = create_test_user()
    price_code = 'setup_addon'
    product_quantity = 2
    products = [
        {
            'code': price_code,
            'quantity': product_quantity,
        }
    ]
    price = create_test_invoice_price(
        code=price_code,
        max_quantity=1,
        min_quantity=0,
    )
    service = StripeService(user=user)

    # act
    with pytest.raises(MaxQuantityReached) as ex:
        service._get_valid_invoice_items(
            products=products
        )

    # assert
    assert ex.value.message == messages.MSG_BL_0013(
        price.max_quantity,
        price.product.name
    )


def test_get_valid_invoice_items__min_quantity_reached__raise_exception(
    mocker
):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    # old subscription data
    old_sub_price_mock = mocker.Mock(currency='usd')
    old_item_mock = mocker.MagicMock(price=old_sub_price_mock)
    old_sub_data = {'items': mocker.Mock(data=[old_item_mock])}
    old_subs_mock = mocker.MagicMock()
    old_subs_mock.__getitem__.side_effect = old_sub_data.__getitem__
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=old_subs_mock
    )
    # end mock init
    user = create_test_user()
    price_code = 'setup_addon'
    product_quantity = 2
    products = [
        {
            'code': price_code,
            'quantity': product_quantity,
        }
    ]
    price = create_test_invoice_price(
        code=price_code,
        min_quantity=3,
        max_quantity=10
    )
    service = StripeService(user=user)

    # act
    with pytest.raises(MinQuantityReached) as ex:
        service._get_valid_invoice_items(
            products=products
        )

    # assert
    assert ex.value.message == messages.MSG_BL_0014(
        price.min_quantity,
        price.product.name
    )


def test_get_customer_portal_link__ok(mocker):

    # arrange
    # mock init
    customer_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
        return_value=customer_mock
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=None
    )
    # end mock init

    account = create_test_account()
    user = create_test_user(account=account)
    cancel_url = 'http://pneumatic.com/some-cancel'

    customer_portal_url = 'https://stripe.com/my-portal'
    session_mock = mocker.Mock(url=customer_portal_url)
    get_valid_subscription_item_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'stripe.billing_portal.session.Session.create',
        return_value=session_mock
    )
    service = StripeService(user=user)

    # act
    result = service.get_customer_portal_link(cancel_url=cancel_url)

    # assert
    assert result == customer_portal_url
    get_valid_subscription_item_mock.assert_called_once_with(
        customer=customer_mock,
        return_url=cancel_url,
    )


def test_update_customer__current__ok(mocker):

    # arrange
    # mock init
    cus_id = 'cus_123'
    customer_mock = mocker.Mock(
        id=cus_id,
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
        return_value=customer_mock
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription'
    )
    # end mock init
    new_acc_name = 'new name'
    new_phone = 'new phone'
    account = create_test_account(name=new_acc_name)
    user = create_test_user(
        account=account,
        phone=new_phone,
        first_name='Lisa',
        last_name='Witson'
    )
    customer_modify_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'stripe.Customer.modify'
    )
    service = StripeService(user=user)

    # act
    service.update_customer()

    # assert
    customer_modify_mock.assert_called_once_with(
        id=cus_id,
        name=new_acc_name,
        phone=new_phone,
        description=f'{user.first_name} {user.last_name}'
    )


def test_update_customer__specified__ok(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
        return_value=None
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription'
    )
    # end mock init
    new_acc_name = 'new name'
    new_phone = 'new phone'
    account = create_test_account(name=new_acc_name)
    user = create_test_user(
        account=account,
        phone=new_phone,
        first_name='Lisa',
        last_name='Witson'
    )
    customer_modify_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'stripe.Customer.modify'
    )
    service = StripeService(user=user)
    cus_id = 'cus_123'
    customer_mock = mocker.Mock(
        id=cus_id
    )
    # act
    service.update_customer(customer_mock)

    # assert
    customer_modify_mock.assert_called_once_with(
        id=cus_id,
        name=new_acc_name,
        phone=new_phone,
        description=f'{user.first_name} {user.last_name}'
    )


def test_create_purchase__off_session__ok(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    payment_method_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method',
        return_value=payment_method_mock
    )
    sub_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=sub_mock
    )
    # end mock init
    user = create_test_user()
    products_mock = mocker.Mock()
    cancel_url = 'http://pneumatic.com/some-cancel'
    success_url = 'http://pneumatic.com/some-success'
    off_session_purchase_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._off_session_purchase'
    )

    service = StripeService(user=user)

    # act
    result = service.create_purchase(
        products=products_mock,
        success_url=success_url,
        cancel_url=cancel_url
    )

    # assert
    assert result is None
    off_session_purchase_mock.assert_called_once_with(
        products=products_mock
    )


def test_create_purchase__off_session_exception__get_checkout_link(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    payment_method_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method',
        return_value=payment_method_mock
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=None
    )
    # end mock init
    user = create_test_user()
    products_mock = mocker.Mock()
    cancel_url = 'http://pneumatic.com/some-cancel'
    success_url = 'http://pneumatic.com/some-success'
    off_session_purchase_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._off_session_purchase',
        side_effect=stripe.error.StripeError('some_message')
    )
    link = 'some link'
    get_checkout_link_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_checkout_link',
        return_value=link
    )
    log_stripe_error_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._log_stripe_error'
    )

    service = StripeService(user=user)

    # act
    result = service.create_purchase(
        products=products_mock,
        success_url=success_url,
        cancel_url=cancel_url
    )

    # assert
    assert result == link
    off_session_purchase_mock.assert_called_once_with(products=products_mock)
    log_stripe_error_mock.assert_called_once()
    get_checkout_link_mock.assert_called_once_with(
        products=products_mock,
        success_url=success_url,
        cancel_url=cancel_url,
    )


def test_create_purchase__off_session_card_error__raise_exception(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    payment_method_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method',
        return_value=payment_method_mock
    )
    subs_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=subs_mock
    )
    # end mock init
    user = create_test_user()
    products_mock = mocker.Mock()
    cancel_url = 'http://pneumatic.com/some-cancel'
    success_url = 'http://pneumatic.com/some-success'
    off_session_purchase_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._off_session_purchase',
        side_effect=stripe.error.CardError(
            message='some_message',
            param='some body',
            code=400
        )
    )
    link = 'some link'
    get_checkout_link_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_checkout_link',
        return_value=link
    )
    log_stripe_error_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._log_stripe_error'
    )

    service = StripeService(user=user)

    # act
    with pytest.raises(CardError) as ex:
        service.create_purchase(
            products=products_mock,
            success_url=success_url,
            cancel_url=cancel_url
        )

    # assert
    assert ex.value.message == messages.MSG_BL_0008
    off_session_purchase_mock.assert_called_once_with(products=products_mock)
    log_stripe_error_mock.assert_called_once()
    get_checkout_link_mock.assert_not_called()


def test_create_purchase__off_session_payment_error__raise_exception(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    payment_method_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method',
        return_value=payment_method_mock
    )
    subs_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=subs_mock
    )
    # end mock init
    user = create_test_user()
    products_mock = mocker.Mock()
    cancel_url = 'http://pneumatic.com/some-cancel'
    success_url = 'http://pneumatic.com/some-success'
    off_session_purchase_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._off_session_purchase',
        side_effect=stripe.error.StripeError('some_message')
    )
    link = 'some link'
    get_checkout_link_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_checkout_link',
        return_value=link
    )
    log_stripe_error_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._log_stripe_error'
    )

    service = StripeService(user=user)

    # act
    with pytest.raises(PaymentError) as ex:
        service.create_purchase(
            products=products_mock,
            success_url=success_url,
            cancel_url=cancel_url
        )

    # assert
    assert ex.value.message == messages.MSG_BL_0009
    off_session_purchase_mock.assert_called_once_with(products=products_mock)
    log_stripe_error_mock.assert_called_once()
    get_checkout_link_mock.assert_not_called()


def test_create_purchase__not_card__return_checkout_link(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method',
        return_value=None
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription'
    )
    # end mock init
    user = create_test_user()
    products_mock = mocker.Mock()
    cancel_url = 'http://pneumatic.com/some-cancel'
    success_url = 'http://pneumatic.com/some-success'
    off_session_purchase_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._off_session_purchase'
    )
    link = 'some link'
    get_checkout_link_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_checkout_link',
        return_value=link
    )
    service = StripeService(user=user)

    # act
    result = service.create_purchase(
        products=products_mock,
        success_url=success_url,
        cancel_url=cancel_url
    )

    # assert
    assert result == link
    off_session_purchase_mock.assert_not_called()
    get_checkout_link_mock.assert_called_once_with(
        products=products_mock,
        success_url=success_url,
        cancel_url=cancel_url
    )


def test_get_payment_method_checkout_link__ok(mocker):

    # arrange
    # mock init
    customer_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
        return_value=customer_mock
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=None
    )
    # end mock init

    account = create_test_account()
    user = create_test_user(account=account)

    cancel_url = 'http://pneumatic.com/some-cancel'
    success_url = 'http://pneumatic.com/some-success'
    success_url_with_token = 'http://pneumatic.com/some-success?token=123'
    get_success_url_with_token_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_success_url_with_token',
        return_value=success_url_with_token
    )
    card_setup_url = 'https://stripe.com/my-portal'
    get_checkout_session_url_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_checkout_session_url',
        return_value=card_setup_url
    )
    service = StripeService(user=user)

    # act
    result = service.get_payment_method_checkout_link(
        success_url=success_url,
        cancel_url=cancel_url,
    )

    # assert
    assert result == card_setup_url
    get_success_url_with_token_mock.assert_called_once_with(url=success_url)
    get_checkout_session_url_mock.assert_called_once_with(
        success_url=success_url_with_token,
        cancel_url=cancel_url,
        mode='setup',
        payment_method_types=['card'],
    )


def test_confirm__ok(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription'
    )
    # end mock init

    account = create_test_account(payment_card_provided=False)
    user = create_test_user(account=account)

    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    account_service_update_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.AccountService.'
        'partial_update'
    )

    service = StripeService(user=user)

    # act
    service.confirm()

    # assert
    account_service_init_mock.assert_called_once_with(
        instance=account,
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    account_service_update_mock.assert_called_once_with(
        payment_card_provided=True,
        force_save=True,
    )


def test_confirm__activate_subscription__from_freemium__ok(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription'
    )
    # end mock init

    account = create_test_account(
        plan=BillingPlanType.FREEMIUM,
        plan_expiration=None,
        payment_card_provided=False,
    )
    user = create_test_user(account=account)

    now_datetime = timezone.now()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'timezone.now',
        return_value=now_datetime
    )
    quantity = 11
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    account_service_update_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.AccountService.'
        'partial_update'
    )
    trial_days = 7
    product_code = 'some premium'
    subscription_data = TokenSubscriptionData(
        billing_plan=product_code,
        max_users=quantity,
        trial_days=trial_days
    )

    is_superuser = True
    auth_type = AuthTokenType.API
    service = StripeService(
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type
    )

    # act
    service.confirm(subscription_data=subscription_data)

    # assert
    account_service_init_mock.assert_called_once_with(
        instance=account,
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type
    )
    account_service_update_mock.assert_called_once_with(
        max_users=quantity,
        plan_expiration=now_datetime + timedelta(hours=1),
        trial_start=now_datetime,
        billing_plan=product_code,
        trial_end=now_datetime + timedelta(days=trial_days),
        payment_card_provided=True,
        tmp_subscription=True,
        force_save=True,
    )


def test_confirm__activate_subscription__from_premium__ok(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription'
    )
    # end mock init

    account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        plan_expiration=timezone.now() - timedelta(days=1),
        payment_card_provided=False,
    )
    user = create_test_user(account=account)

    now_datetime = timezone.now()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'timezone.now',
        return_value=now_datetime
    )
    quantity = 11
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    account_service_update_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.AccountService.'
        'partial_update'
    )
    trial_days = 7
    product_code = 'some premium'
    subscription_data = TokenSubscriptionData(
        billing_plan=product_code,
        max_users=quantity,
        trial_days=trial_days
    )

    is_superuser = True
    auth_type = AuthTokenType.API
    service = StripeService(
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type
    )

    # act
    service.confirm(subscription_data=subscription_data)

    # assert
    account_service_init_mock.assert_called_once_with(
        instance=account,
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type
    )
    account_service_update_mock.assert_called_once_with(
        max_users=quantity,
        plan_expiration=now_datetime + timedelta(hours=1),
        trial_start=now_datetime,
        trial_end=now_datetime + timedelta(days=trial_days),
        billing_plan=product_code,
        payment_card_provided=True,
        tmp_subscription=True,
        force_save=True,
    )


def test_confirm__subscription_already_activated__skip(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription'
    )
    # end mock init

    account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        plan_expiration=timezone.now() + timedelta(days=7),
        payment_card_provided=False,
    )
    user = create_test_user(account=account)

    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    account_service_update_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.AccountService.'
        'partial_update'
    )
    subscription_data = TokenSubscriptionData(
        billing_plan='some premium',
        max_users=10,
        trial_days=7
    )
    service = StripeService(user=user)

    # act
    service.confirm(subscription_data=subscription_data)

    # assert
    account_service_init_mock.assert_called_once_with(
        instance=account,
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    account_service_update_mock.assert_called_once_with(
        payment_card_provided=True,
        force_save=True,
    )


def test_increase_subscription__ok(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method',
    )
    # old subscription data
    old_price_id = 'price_old1213ad'
    old_sub_price_mock = mocker.Mock(id=old_price_id)
    old_item_mock = mocker.MagicMock(
        id=old_price_id,
        price=old_sub_price_mock
    )
    old_sub_data = {'items': mocker.Mock(data=[old_item_mock])}
    sub_id = 'sub_123AD'
    old_subs_mock = mocker.MagicMock(id=sub_id)
    old_subs_mock.__getitem__.side_effect = old_sub_data.__getitem__
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=old_subs_mock
    )
    # end mock init
    old_plan = BillingPlanType.PREMIUM
    new_plan_expiration = timezone.now() + timedelta(days=30)
    account = create_test_account(
        payment_card_provided=False,
        plan=old_plan,
        plan_expiration=new_plan_expiration
    )
    user = create_test_user(account=account)
    new_quantity = 15

    new_subscription = mocker.Mock()
    stripe_subscription_modify_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'stripe.Subscription.modify',
        return_value=new_subscription
    )
    subscription_details_mock = mocker.Mock()
    get_subscription_details_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService.get_subscription_details',
        return_value=subscription_details_mock
    )
    account_subs_service_update = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'AccountSubscriptionService.update'
    )
    service = StripeService(user=user)

    # act
    service.increase_subscription(quantity=new_quantity)

    # assert
    stripe_subscription_modify_mock.assert_called_once_with(
        id=sub_id,
        items=[
            {
                "id": old_item_mock.id,
                "quantity": new_quantity,
            }
        ],
        trial_end='now',
        metadata={'account_id': account.id},
        description='Main'
    )
    get_subscription_details_mock.assert_called_once_with(new_subscription)
    account_subs_service_update.assert_called_once_with(
        details=subscription_details_mock,
    )


def test_increase_subscription__tenant__ok(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method',
    )
    # old subscription data
    old_price_id = 'price_old1213ad'
    old_sub_price_mock = mocker.Mock(id=old_price_id)
    old_item_mock = mocker.MagicMock(
        id=old_price_id,
        price=old_sub_price_mock
    )
    old_sub_data = {'items': mocker.Mock(data=[old_item_mock])}
    sub_id = 'sub_123AD'
    old_subs_mock = mocker.MagicMock(id=sub_id)
    old_subs_mock.__getitem__.side_effect = old_sub_data.__getitem__
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=old_subs_mock
    )
    # end mock init
    master_account = create_test_account(
        trial_ended=False,
        lease_level=LeaseLevel.STANDARD
    )
    user = create_test_user(account=master_account)
    tenant_name = 'some teant name'
    tenant_account = create_test_account(
        lease_level=LeaseLevel.TENANT,
        master_account=master_account,
        name='tenant',
        tenant_name=tenant_name
    )

    new_quantity = 2

    new_subscription = mocker.Mock()
    stripe_subscription_modify_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'stripe.Subscription.modify',
        return_value=new_subscription
    )
    subscription_details_mock = mocker.Mock()
    get_subscription_details_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService.get_subscription_details',
        return_value=subscription_details_mock
    )
    account_subs_service_update = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'AccountSubscriptionService.update'
    )
    service = StripeService(
        user=user,
        subscription_account=tenant_account
    )

    # act
    service.increase_subscription(quantity=new_quantity)

    # assert
    stripe_subscription_modify_mock.assert_called_once_with(
        id=sub_id,
        items=[
            {
                "id": old_item_mock.id,
                "quantity": new_quantity,
            }
        ],
        trial_end='now',
        metadata={'account_id': tenant_account.id},
        description=tenant_name
    )
    get_subscription_details_mock.assert_called_once_with(new_subscription)
    account_subs_service_update.assert_called_once_with(
        details=subscription_details_mock,
    )


def test_increase_subscription__not_exist__raise_exception(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method',
    )
    # old subscription data
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=None
    )
    # end mock init
    account = create_test_account()
    user = create_test_user(account=account)
    new_quantity = 15

    service = StripeService(user=user)

    # act
    with pytest.raises(SubscriptionNotExist) as ex:
        service.increase_subscription(quantity=new_quantity)

    # assert
    assert ex.value.message == messages.MSG_BL_0005


def test_cancel_subscription__ok(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method',
    )
    subs_id = 'sub_123ad'
    subscription_mock = mocker.Mock(id=subs_id)
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=subscription_mock
    )
    # end mock init

    account = create_test_account()
    user = create_test_user(account=account)
    new_subscription = mocker.Mock()
    stripe_subscription_modify_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'stripe.Subscription.modify',
        return_value=new_subscription
    )
    subscription_details_mock = mocker.Mock(plan_expiration=mocker.Mock())
    get_subscription_details_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService.get_subscription_details',
        return_value=subscription_details_mock
    )
    account_subs_service_cancel = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'AccountSubscriptionService.cancel'
    )
    service = StripeService(user=user)

    # act
    service.cancel_subscription()

    # assert
    stripe_subscription_modify_mock.assert_called_once_with(
        id=subs_id,
        cancel_at_period_end=True
    )
    get_subscription_details_mock.assert_called_once_with(new_subscription)
    account_subs_service_cancel.assert_called_once_with(
        subscription_details_mock.plan_expiration
    )


def test_cancel_subscription__not_subscription__skip(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=None
    )
    # end mock init

    user = create_test_user()
    stripe_subscription_modify_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'stripe.Subscription.modify',
    )
    get_subscription_details_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService.get_subscription_details',
    )
    account_subs_service_cancel = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'AccountSubscriptionService.cancel'
    )
    service = StripeService(user=user)

    # act
    service.cancel_subscription()

    # assert
    stripe_subscription_modify_mock.assert_not_called()
    get_subscription_details_mock.assert_not_called()
    account_subs_service_cancel.assert_not_called()


def test_terminate_subscription__ok(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method',
    )
    subscription_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=subscription_mock
    )
    # end mock init

    account = create_test_account()
    user = create_test_user(account=account)
    account_subs_service_downgrade_to_free_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'AccountSubscriptionService.downgrade_to_free'
    )
    service = StripeService(user=user)

    # act
    service.terminate_subscription()

    # assert
    subscription_mock.cancel.assert_called_once()
    account_subs_service_downgrade_to_free_mock.assert_called_once()


def test_terminate_subscription__not_subscription__ok(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=None
    )
    # end mock init

    account = create_test_account()
    user = create_test_user(account=account)
    account_subs_service_terminate_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'AccountSubscriptionService.downgrade_to_free'
    )
    service = StripeService(user=user)

    # act
    service.terminate_subscription()

    # assert
    account_subs_service_terminate_mock.assert_called_once()


def test_get_payment_method__ok(mocker):

    # arrange
    # mock init
    customer_mock = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
        return_value=customer_mock
    )
    card_last4 = '6644'
    card_brand = 'MasterCard'
    method_mock = mocker.Mock(
        card={
            'last4': card_last4,
            'brand': card_brand,
        }
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method',
        return_value=method_mock
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription'
    )
    # end mock init

    account = create_test_account(payment_card_provided=False)
    user = create_test_user(account=account)
    service = StripeService(user=user)

    # act
    result = service.get_payment_method()

    # assert
    assert result['last4'] == card_last4
    assert result['brand'] == card_brand


def test_update_subscription_description__not_tenant__skip(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method',
    )
    subs_id = 'sub_123'
    description = 'old'
    subscription_mock = mocker.Mock(
        description=description,
        id=subs_id
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=subscription_mock
    )
    sub_modify_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'stripe.Subscription.modify'
    )

    # end mock init
    account = create_test_account(lease_level=LeaseLevel.STANDARD)
    user = create_test_user(account=account)
    service = StripeService(user=user)

    # act
    service.update_subscription_description()

    # assert
    sub_modify_mock.assert_not_called()


def test_update_subscription_description__tenant__ok(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer'
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method'
    )
    subs_id = 'sub_123'
    subscription_mock = mocker.Mock(
        description='old',
        id=subs_id
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=subscription_mock
    )
    sub_modify_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'stripe.Subscription.modify'
    )
    # end mock init
    master_account = create_test_account(lease_level=LeaseLevel.STANDARD)
    user = create_test_user(account=master_account, email='owner@test.test')
    new_tenant_name = 'new'
    tenant = create_test_account(
        lease_level=LeaseLevel.TENANT,
        master_account=master_account,
        tenant_name=new_tenant_name,
        name='Tenant'
    )
    service = StripeService(
        user=user,
        subscription_account=tenant
    )

    # act
    service.update_subscription_description()

    # assert
    sub_modify_mock.assert_called_once_with(
        id=subs_id,
        description=new_tenant_name
    )


def test_update_subscription_description__not_subs__skip(mocker):

    # arrange
    # mock init
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription',
        return_value=None
    )
    # end mock init
    master_account = create_test_account(lease_level=LeaseLevel.STANDARD)
    user = create_test_user(account=master_account, email='owner@test.test')
    new_tenant_name = 'new'
    tenant = create_test_account(
        lease_level=LeaseLevel.TENANT,
        master_account=master_account,
        tenant_name=new_tenant_name,
        name='Tenant'
    )
    service = StripeService(
        user=user,
        subscription_account=tenant
    )
    sub_modify_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'stripe.Subscription.modify'
    )

    # act
    service.update_subscription_description()

    # arrange
    sub_modify_mock.assert_not_called()


def test_get_checkout_session_url__create__ok(mocker):

    # arrange
    # mock init
    stripe_id = 'cus_123'
    customer_mock = mocker.Mock(stripe_id=stripe_id)
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
        return_value=customer_mock
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription'
    )
    mocker.patch.object(
        AccountSubscriptionService,
        attribute='__init__',
        return_value=None
    )
    # end mock init

    checkout_session_list_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'stripe.checkout.Session.list',
        return_value=[]
    )

    checkout_link = 'http://stripe.com/some-link'
    session = mocker.Mock(url=checkout_link)
    checkout_session_create_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'stripe.checkout.Session.create',
        return_value=session
    )
    idempotency_key = '12312asdw'
    get_idempotency_key_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_idempotency_key',
        return_value=idempotency_key
    )
    account = create_test_account(payment_card_provided=False)
    user = create_test_user(account=account)
    service = StripeService(user=user)

    cancel_url = 'http://pneumatic.com/some-cancel'
    success_url = 'http://pneumatic.com/some-success'

    # act
    url = service._get_checkout_session_url(
        success_url=success_url,
        cancel_url=cancel_url,
        mode='subscription',
        allow_promotion_codes=True,
    )

    # assert
    assert url == checkout_link
    checkout_session_list_mock.assert_called_once_with(
        customer=customer_mock,
        status='open',
    )
    get_idempotency_key_mock.assert_called_once_with(
        mode='subscription',
        allow_promotion_codes=True,
        stripe_id=stripe_id,
        account_id=account.id
    )
    checkout_session_create_mock.assert_called_once_with(
        customer=customer_mock,
        client_reference_id=idempotency_key,
        cancel_url=cancel_url,
        success_url=success_url,
        mode='subscription',
        allow_promotion_codes=True,
    )


def test_get_checkout_session_url__duplicate__return_existent(mocker):

    # arrange
    # mock init
    stripe_id = 'cus_321'
    customer_mock = mocker.Mock(stripe_id=stripe_id)
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_or_create_customer',
        return_value=customer_mock
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_payment_method',
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_current_subscription'
    )
    mocker.patch.object(
        AccountSubscriptionService,
        attribute='__init__',
        return_value=None
    )
    # end mock init

    idempotency_key = '12312asdw'
    get_idempotency_key_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService._get_idempotency_key',
        return_value=idempotency_key
    )

    checkout_link = 'http://stripe.com/some-link'
    session_mock = mocker.Mock(
        url=checkout_link,
        client_reference_id=idempotency_key
    )
    another_session_mock = mocker.Mock(
        url='http://stripe.com/another-link',
        client_reference_id=None
    )
    checkout_session_list_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'stripe.checkout.Session.list',
        return_value=[
            another_session_mock,
            session_mock,
        ]
    )

    checkout_session_create_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'stripe.checkout.Session.create'
    )
    account = create_test_account(payment_card_provided=False)
    user = create_test_user(account=account)
    service = StripeService(user=user)

    cancel_url = 'http://pneumatic.com/some-cancel'
    success_url = 'http://pneumatic.com/some-success'

    # act
    url = service._get_checkout_session_url(
        success_url=success_url,
        cancel_url=cancel_url,
        mode='subscription',
        allow_promotion_codes=True,
    )

    # assert
    assert url == checkout_link
    checkout_session_list_mock.assert_called_once_with(
        customer=customer_mock,
        status='open',
    )
    get_idempotency_key_mock.assert_called_once_with(
        mode='subscription',
        allow_promotion_codes=True,
        stripe_id=stripe_id,
        account_id=account.id
    )
    checkout_session_create_mock.assert_not_called()
