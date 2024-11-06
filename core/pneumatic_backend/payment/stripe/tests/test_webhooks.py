import pytest
import stripe
from datetime import timedelta
from django.utils import timezone
from pneumatic_backend.payment.enums import (
    BillingPeriod,
    PriceType,
    PriceStatus,
)
from pneumatic_backend.payment.models import (
    Product,
    Price
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_account,
    create_test_user,
)
from pneumatic_backend.payment.tests.fixtures import (
    create_test_product,
    create_test_recurring_price,
    create_test_invoice_price
)
from pneumatic_backend.payment.stripe.exceptions import (
    WebhookServiceException,
    AccountNotFound,
    AccountOwnerNotFound,
    NotFoundAccountForSubscription,
)
from pneumatic_backend.payment.stripe.webhooks import (
    WebhookService,
)
from pneumatic_backend.payment.services.account import (
    AccountSubscriptionService
)
from pneumatic_backend.accounts.enums import LeaseLevel
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.payment import messages
from pneumatic_backend.utils.logging import SentryLogLevel
from pneumatic_backend.accounts.services import UserService


pytestmark = pytest.mark.django_db


def test_get_valid_webhook_account_by_stripe_id__ok(mocker):

    # arrange
    stripe_id = 'cus_23123'
    account = create_test_account(stripe_id=stripe_id)
    create_test_user(account=account, is_account_owner=True)
    get_account_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService._get_account',
        return_value=account
    )
    service = WebhookService()

    # act
    result = service._get_valid_webhook_account_by_stripe_id(stripe_id)

    # assert
    assert result == account
    get_account_mock.assert_called_once_with(stripe_id)


def test_get_valid_webhook_account_by_stripe_id__not_account__raise(mocker):

    # arrange
    stripe_id = 'cus_23123'
    get_account_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService._get_account',
        return_value=None
    )
    service = WebhookService()

    # act
    with pytest.raises(AccountNotFound) as ex:
        service._get_valid_webhook_account_by_stripe_id(stripe_id)

    # assert
    assert ex.value.message == messages.MSG_BL_0019
    assert ex.value.details == {'stripe_id': stripe_id}
    get_account_mock.assert_called_once_with(stripe_id)


def test_get_valid_webhook_account_by_stripe_id__not_owner__raise(mocker):

    # arrange
    stripe_id = 'cus_23123'
    account = create_test_account(stripe_id=stripe_id)
    get_account_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService._get_account',
        return_value=account
    )
    service = WebhookService()

    # act
    with pytest.raises(AccountOwnerNotFound) as ex:
        service._get_valid_webhook_account_by_stripe_id(stripe_id)

    # assert
    assert ex.value.message == messages.MSG_BL_0020
    assert ex.value.details == {'account_id': account.id}
    get_account_mock.assert_called_once_with(stripe_id)


def test_get_valid_webhook_account_by_subs__ok(mocker):

    # arrange
    stripe_id = 'cus_123sd'
    account = create_test_account(stripe_id=stripe_id)
    create_test_user(account=account, is_account_owner=True)
    subscription_mock = mocker.Mock()
    subscription_mock.customer = stripe_id
    get_valid_webhook_account_by_stripe_id_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService._get_valid_webhook_account_by_stripe_id',
        return_value=account
    )
    get_account_for_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService._get_account_for_subscription',
        return_value=account
    )
    service = WebhookService()

    # act
    result = service._get_valid_webhook_account_by_subs(subscription_mock)

    # assert
    assert result == account
    get_valid_webhook_account_by_stripe_id_mock.assert_called_once_with(
        stripe_id=stripe_id
    )
    get_account_for_subscription_mock.assert_called_once_with(
        account=account,
        subscription=subscription_mock
    )


def test_get_valid_webhook_account_by_subs__tenant__ok(mocker):

    # arrange
    master_account = create_test_account()
    create_test_user(account=master_account, is_account_owner=True)
    tenant = create_test_account(
        name='Tenant',
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    create_test_user(
        account=tenant,
        is_account_owner=True,
        email='tenant@owner.com'
    )

    stripe_id = 'cus_123sd'
    subscription_mock = mocker.Mock()
    subscription_mock.customer = stripe_id
    get_valid_webhook_account_by_stripe_id_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService._get_valid_webhook_account_by_stripe_id',
        return_value=master_account
    )
    get_account_for_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService._get_account_for_subscription',
        return_value=tenant
    )
    service = WebhookService()

    # act
    result = service._get_valid_webhook_account_by_subs(subscription_mock)

    # assert
    assert result == tenant
    get_valid_webhook_account_by_stripe_id_mock.assert_called_once_with(
        stripe_id=stripe_id
    )
    get_account_for_subscription_mock.assert_called_once_with(
        account=master_account,
        subscription=subscription_mock
    )


def test_get_valid_webhook_account_by_subs__tenant_not_account__raise(mocker):

    # arrange
    master_account = create_test_account()
    create_test_user(account=master_account, is_account_owner=True)
    stripe_id = 'cus_123sd'
    subscription_mock = mocker.Mock()
    subscription_mock.id = 'sub_123'
    subscription_mock.customer = stripe_id
    get_valid_webhook_account_by_stripe_id_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService._get_valid_webhook_account_by_stripe_id',
        return_value=master_account
    )
    get_account_for_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService._get_account_for_subscription',
        return_value=None
    )
    service = WebhookService()

    # act
    with pytest.raises(AccountNotFound) as ex:
        service._get_valid_webhook_account_by_subs(subscription_mock)

    # assert
    assert ex.value.message == messages.MSG_BL_0019
    assert ex.value.details == {'subs_id': subscription_mock.id}
    get_valid_webhook_account_by_stripe_id_mock.assert_called_once_with(
        stripe_id=stripe_id
    )
    get_account_for_subscription_mock.assert_called_once_with(
        account=master_account,
        subscription=subscription_mock
    )


def test_get_valid_webhook_account_by_subs__tenant_not_account_owner__raise(
    mocker
):

    # arrange
    master_account = create_test_account()
    create_test_user(account=master_account, is_account_owner=True)
    tenant = create_test_account(
        name='Tenant',
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    stripe_id = 'cus_123sd'
    subscription_mock = mocker.Mock()
    subscription_mock.id = 'sub_123'
    subscription_mock.customer = stripe_id
    get_valid_webhook_account_by_stripe_id_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService._get_valid_webhook_account_by_stripe_id',
        return_value=master_account
    )
    get_account_for_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService._get_account_for_subscription',
        return_value=tenant
    )
    service = WebhookService()

    # act
    with pytest.raises(AccountOwnerNotFound) as ex:
        service._get_valid_webhook_account_by_subs(subscription_mock)

    # assert
    assert ex.value.message == messages.MSG_BL_0020
    assert ex.value.details == {'account_id': tenant.id}
    get_valid_webhook_account_by_stripe_id_mock.assert_called_once_with(
        stripe_id=stripe_id
    )
    get_account_for_subscription_mock.assert_called_once_with(
        account=master_account,
        subscription=subscription_mock
    )


def test_payment_method_attached__ok(mocker):

    # arrange
    customer_stripe_id = "cus_Nx9XuHa4xteob3"
    method_stripe_id = 'pm_1NG6tmBM2UVM1VfG3Gnat77h'
    data = {
      "id": "evt_1NG6tnBM2UVM1VfGibM6HakT",
      "object": "event",
      "api_version": "2022-11-15",
      "created": 1686084879,
      "data": {
        "object": {
          "id": method_stripe_id,
          "object": "payment_method",
          "billing_details": {
            "address": {
              "city": None,
              "country": "US",
              "line1": None,
              "line2": None,
              "postal_code": "35004",
              "state": None
            },
            "email": "admin@pneumatic.app",
            "name": "New York",
            "phone": None
          },
          "card": {
            "brand": "discover",
            "checks": {
              "address_line1_check": None,
              "address_postal_code_check": "pass",
              "cvc_check": "pass"
            },
            "country": "US",
            "exp_month": 1,
            "exp_year": 2027,
            "fingerprint": "J4PgUuXvtxWhPxSr",
            "funding": "credit",
            "generated_from": None,
            "last4": "1117",
            "networks": {
              "available": [
                "discover"
              ],
              "preferred": None
            },
            "three_d_secure_usage": {
              "supported": True
            },
            "wallet": None
          },
          "created": 1686084878,
          "customer": customer_stripe_id,
          "livemode": False,
          "metadata": {
          },
          "type": "card"
        }
      },
      "livemode": False,
      "pending_webhooks": 1,
      "request": {
        "id": "req_bvoxgSnbqQINqB",
        "idempotency_key": "bd41da5f-32ff-4326-8605-f2349d505630"
      },
      "type": "payment_method.attached"
    }
    event = stripe.Event.construct_from(
        values=data,
        key='!!@#'
    )
    set_default_payment_method_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService._set_default_payment_method'
    )
    method = mocker.Mock(customer=customer_stripe_id)
    get_method_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService._get_payment_method',
        return_value=method
    )
    customer = mocker.Mock()
    get_customer_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService._get_customer',
        return_value=customer
    )
    service = WebhookService()

    # act
    service._payment_method_attached(event)

    # assert
    get_method_mock.assert_called_once_with(method_stripe_id)
    get_customer_mock.assert_called_once_with(customer_stripe_id)
    set_default_payment_method_mock.assert_called_once_with(
        method=method,
        customer=customer,
    )


def test_customer_subscription_created__ok(mocker):

    # arrange
    customer_stripe_id = "cus_Nx9XuHa4xteob3"
    account = create_test_account(stripe_id=customer_stripe_id)
    user = create_test_user(account=account)
    subscription_stripe_id = 'sub_1NG6tmBM2UVM1VfG3Gnat77h'
    data = {
      "id": "evt_1NFzyFBM2UVM1VfG56peU3IN",
      "object": "event",
      "api_version": "2022-11-15",
      "created": 1686058246,
      "data": {
        "object": {
          "id": subscription_stripe_id,
          "object": "subscription",
          "application": None,
          "application_fee_percent": None,
          "automatic_tax": {
            "enabled": False
          },
          "billing_cycle_anchor": 1686663046,
          "billing_thresholds": None,
          "cancel_at": None,
          "cancel_at_period_end": False,
          "canceled_at": None,
          "cancellation_details": {
            "comment": None,
            "feedback": None,
            "reason": None
          },
          "collection_method": "charge_automatically",
          "created": 1686058246,
          "currency": "usd",
          "current_period_end": 1686663046,
          "current_period_start": 1686058246,
          "customer": "cus_O246vtkS23giHf",
          "days_until_due": None,
          "default_payment_method": "pm_1NFzyCBM2UVM1VfGuHIwB8r4",
          "default_source": None,
          "default_tax_rates": [
          ],
          "description": None,
          "discount": None,
          "ended_at": None,
          "items": {
            "object": "list",
            "data": [
              {
                "id": "si_O246JOhqACnVAp",
                "object": "subscription_item",
                "billing_thresholds": None,
                "created": 1686058246,
                "metadata": {
                },
                "plan": {
                  "id": "price_1N8JnDBM2UVM1VfGDN6IsDDg",
                  "object": "plan",
                  "active": True,
                  "aggregate_usage": None,
                  "amount": 1000,
                  "amount_decimal": "1000",
                  "billing_scheme": "per_unit",
                  "created": 1684227819,
                  "currency": "usd",
                  "interval": "month",
                  "interval_count": 1,
                  "livemode": False,
                  "metadata": {
                  },
                  "nickname": None,
                  "product": "prod_Nu83RUXCw93YJs",
                  "tiers_mode": None,
                  "transform_usage": None,
                  "trial_period_days": 7,
                  "usage_type": "licensed"
                },
                "price": {
                  "id": "price_1N8JnDBM2UVM1VfGDN6IsDDg",
                  "object": "price",
                  "active": True,
                  "billing_scheme": "per_unit",
                  "created": 1684227819,
                  "currency": "usd",
                  "custom_unit_amount": None,
                  "livemode": False,
                  "lookup_key": None,
                  "metadata": {
                  },
                  "nickname": None,
                  "product": "prod_Nu83RUXCw93YJs",
                  "recurring": {
                    "aggregate_usage": None,
                    "interval": "month",
                    "interval_count": 1,
                    "trial_period_days": 7,
                    "usage_type": "licensed"
                  },
                  "tax_behavior": "unspecified",
                  "tiers_mode": None,
                  "transform_quantity": None,
                  "type": "recurring",
                  "unit_amount": 1000,
                  "unit_amount_decimal": "1000"
                },
                "quantity": 5,
                "subscription": "sub_1NFzyEBM2UVM1VfGJdLHZKWx",
                "tax_rates": [
                ]
              }
            ],
            "has_more": False,
            "total_count": 1,
            "url": "/v1/subscription_items?subscription=sub_1NFzyJdLHZKWx"
          },
          "latest_invoice": "in_1NFzyEBM2UVM1VfGuP3XdHle",
          "livemode": False,
          "metadata": {
          },
          "next_pending_invoice_item_invoice": None,
          "on_behalf_of": None,
          "pause_collection": None,
          "payment_settings": {
            "payment_method_options": None,
            "payment_method_types": None,
            "save_default_payment_method": "off"
          },
          "pending_invoice_item_interval": None,
          "pending_setup_intent": None,
          "pending_update": None,
          "plan": {
            "id": "price_1N8JnDBM2UVM1VfGDN6IsDDg",
            "object": "plan",
            "active": True,
            "aggregate_usage": None,
            "amount": 1000,
            "amount_decimal": "1000",
            "billing_scheme": "per_unit",
            "created": 1684227819,
            "currency": "usd",
            "interval": "month",
            "interval_count": 1,
            "livemode": False,
            "metadata": {
            },
            "nickname": None,
            "product": "prod_Nu83RUXCw93YJs",
            "tiers_mode": None,
            "transform_usage": None,
            "trial_period_days": 7,
            "usage_type": "licensed"
          },
          "quantity": 5,
          "schedule": None,
          "start_date": 1686058246,
          "status": "trialing",
          "test_clock": None,
          "transfer_data": None,
          "trial_end": 1686663046,
          "trial_settings": {
            "end_behavior": {
              "missing_payment_method": "create_invoice"
            }
          },
          "trial_start": 1686058246
        }
      },
      "livemode": False,
      "pending_webhooks": 1,
      "request": {
        "id": None,
        "idempotency_key": None
      },
      "type": "customer.subscription.created"
    }
    event = stripe.Event.construct_from(
        values=data,
        key='!!@#'
    )
    customer_mock = mocker.Mock()
    subscription_mock = mocker.Mock()
    subscription_mock.customer = customer_mock
    get_subscription_by_id_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService._get_subscription_by_id',
        return_value=subscription_mock
    )
    get_valid_webhook_account_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService._get_valid_webhook_account_by_subs',
        return_value=account
    )
    subscription_details_mock = mocker.Mock()
    get_subscription_details_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService.get_subscription_details',
        return_value=subscription_details_mock
    )
    account_service_init_mock = mocker.patch.object(
        AccountSubscriptionService,
        attribute='__init__',
        return_value=None
    )
    account_service_create_mock = mocker.patch(
        'pneumatic_backend.payment.services.account.'
        'AccountSubscriptionService.create'
    )
    service = WebhookService()

    # act
    service._customer_subscription_created(event)

    # assert
    get_subscription_by_id_mock.assert_called_once_with(subscription_stripe_id)
    get_valid_webhook_account_mock.assert_called_once_with(subscription_mock)
    get_subscription_details_mock.assert_called_once_with(subscription_mock)
    account_service_init_mock.assert_called_once_with(
        instance=account,
        user=user,
        auth_type=AuthTokenType.WEBHOOK,
    )
    account_service_create_mock.assert_called_once_with(
        details=subscription_details_mock,
        payment_card_provided=True
    )


def test_customer_subscription_created__tenant__ok(mocker):

    # arrange
    master_account = create_test_account()
    create_test_user(account=master_account)
    tenant = create_test_account(
        name='Tenant',
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    tenant_owner = create_test_user(
        account=tenant,
        is_account_owner=True,
        email='tenant@owner.com'
    )

    subscription_stripe_id = 'sub_1NG6tmBM2UVM1VfG3Gnat77h'
    data = {
      "id": "evt_1NFzyFBM2UVM1VfG56peU3IN",
      "object": "event",
      "api_version": "2022-11-15",
      "created": 1686058246,
      "data": {
        "object": {
          "id": subscription_stripe_id,
          "object": "subscription",
          "application": None,
          "application_fee_percent": None,
          "automatic_tax": {
            "enabled": False
          },
          "billing_cycle_anchor": 1686663046,
          "billing_thresholds": None,
          "cancel_at": None,
          "cancel_at_period_end": False,
          "canceled_at": None,
          "cancellation_details": {
            "comment": None,
            "feedback": None,
            "reason": None
          },
          "collection_method": "charge_automatically",
          "created": 1686058246,
          "currency": "usd",
          "current_period_end": 1686663046,
          "current_period_start": 1686058246,
          "customer": "cus_O246vtkS23giHf",
          "days_until_due": None,
          "default_payment_method": "pm_1NFzyCBM2UVM1VfGuHIwB8r4",
          "default_source": None,
          "default_tax_rates": [
          ],
          "description": None,
          "discount": None,
          "ended_at": None,
          "items": {
            "object": "list",
            "data": [
              {
                "id": "si_O246JOhqACnVAp",
                "object": "subscription_item",
                "billing_thresholds": None,
                "created": 1686058246,
                "metadata": {
                },
                "plan": {
                  "id": "price_1N8JnDBM2UVM1VfGDN6IsDDg",
                  "object": "plan",
                  "active": True,
                  "aggregate_usage": None,
                  "amount": 1000,
                  "amount_decimal": "1000",
                  "billing_scheme": "per_unit",
                  "created": 1684227819,
                  "currency": "usd",
                  "interval": "month",
                  "interval_count": 1,
                  "livemode": False,
                  "metadata": {
                  },
                  "nickname": None,
                  "product": "prod_Nu83RUXCw93YJs",
                  "tiers_mode": None,
                  "transform_usage": None,
                  "trial_period_days": 7,
                  "usage_type": "licensed"
                },
                "price": {
                  "id": "price_1N8JnDBM2UVM1VfGDN6IsDDg",
                  "object": "price",
                  "active": True,
                  "billing_scheme": "per_unit",
                  "created": 1684227819,
                  "currency": "usd",
                  "custom_unit_amount": None,
                  "livemode": False,
                  "lookup_key": None,
                  "metadata": {
                  },
                  "nickname": None,
                  "product": "prod_Nu83RUXCw93YJs",
                  "recurring": {
                    "aggregate_usage": None,
                    "interval": "month",
                    "interval_count": 1,
                    "trial_period_days": 7,
                    "usage_type": "licensed"
                  },
                  "tax_behavior": "unspecified",
                  "tiers_mode": None,
                  "transform_quantity": None,
                  "type": "recurring",
                  "unit_amount": 1000,
                  "unit_amount_decimal": "1000"
                },
                "quantity": 5,
                "subscription": "sub_1NFzyEBM2UVM1VfGJdLHZKWx",
                "tax_rates": [
                ]
              }
            ],
            "has_more": False,
            "total_count": 1,
            "url": "/v1/subscription_items?subscription=sub_1NFzyJdLHZKWx"
          },
          "latest_invoice": "in_1NFzyEBM2UVM1VfGuP3XdHle",
          "livemode": False,
          "metadata": {
          },
          "next_pending_invoice_item_invoice": None,
          "on_behalf_of": None,
          "pause_collection": None,
          "payment_settings": {
            "payment_method_options": None,
            "payment_method_types": None,
            "save_default_payment_method": "off"
          },
          "pending_invoice_item_interval": None,
          "pending_setup_intent": None,
          "pending_update": None,
          "plan": {
            "id": "price_1N8JnDBM2UVM1VfGDN6IsDDg",
            "object": "plan",
            "active": True,
            "aggregate_usage": None,
            "amount": 1000,
            "amount_decimal": "1000",
            "billing_scheme": "per_unit",
            "created": 1684227819,
            "currency": "usd",
            "interval": "month",
            "interval_count": 1,
            "livemode": False,
            "metadata": {
            },
            "nickname": None,
            "product": "prod_Nu83RUXCw93YJs",
            "tiers_mode": None,
            "transform_usage": None,
            "trial_period_days": 7,
            "usage_type": "licensed"
          },
          "quantity": 5,
          "schedule": None,
          "start_date": 1686058246,
          "status": "trialing",
          "test_clock": None,
          "transfer_data": None,
          "trial_end": 1686663046,
          "trial_settings": {
            "end_behavior": {
              "missing_payment_method": "create_invoice"
            }
          },
          "trial_start": 1686058246
        }
      },
      "livemode": False,
      "pending_webhooks": 1,
      "request": {
        "id": None,
        "idempotency_key": None
      },
      "type": "customer.subscription.created"
    }
    event = stripe.Event.construct_from(
        values=data,
        key='!!@#'
    )
    customer_mock = mocker.Mock()
    subscription_mock = mocker.Mock()
    subscription_mock.customer = customer_mock
    get_subscription_by_id_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService._get_subscription_by_id',
        return_value=subscription_mock
    )
    get_valid_webhook_account_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService._get_valid_webhook_account_by_subs',
        return_value=tenant
    )
    subscription_details_mock = mocker.Mock()
    get_subscription_details_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService.get_subscription_details',
        return_value=subscription_details_mock
    )
    account_service_init_mock = mocker.patch.object(
        AccountSubscriptionService,
        attribute='__init__',
        return_value=None
    )
    account_service_create_mock = mocker.patch(
        'pneumatic_backend.payment.services.account.'
        'AccountSubscriptionService.create'
    )
    service = WebhookService()

    # act
    service._customer_subscription_created(event)

    # assert
    get_subscription_by_id_mock.assert_called_once_with(subscription_stripe_id)
    get_valid_webhook_account_mock.assert_called_once_with(subscription_mock)
    get_subscription_details_mock.assert_called_once_with(subscription_mock)
    account_service_init_mock.assert_called_once_with(
        instance=tenant,
        user=tenant_owner,
        auth_type=AuthTokenType.WEBHOOK,
    )
    account_service_create_mock.assert_called_once_with(
        details=subscription_details_mock,
        payment_card_provided=True
    )


def test_customer_subscription_updated__update__ok(mocker):

    # arrange
    customer_stripe_id = "cus_Nx9XuHa4xteob3"
    account = create_test_account(stripe_id=customer_stripe_id)
    user = create_test_user(account=account)
    subscription_stripe_id = 'sub_1NG6tmBM2UVM1VfG3Gnat77h'
    cancel_at = None
    data = {
      "id": "evt_1NG6HSBM2UVM1VfG5ChrCp3O",
      "object": "event",
      "api_version": "2022-11-15",
      "created": 1686082502,
      "data": {
        "object": {
          "id": subscription_stripe_id,
          "object": "subscription",
          "application": None,
          "application_fee_percent": None,
          "automatic_tax": {
            "enabled": False
          },
          "billing_cycle_anchor": 1686121200,
          "billing_thresholds": None,
          "cancel_at": cancel_at,
          "cancel_at_period_end": False,
          "canceled_at": 1686082502,
          "cancellation_details": {
            "comment": None,
            "feedback": None,
            "reason": "cancellation_requested"
          },
          "collection_method": "charge_automatically",
          "created": 1685949994,
          "currency": "usd",
          "current_period_end": 1686121200,
          "current_period_start": 1685949994,
          "customer": "cus_O1ax86Phph0xyw",
          "days_until_due": None,
          "default_payment_method": "pm_1NFXoCBM2UVM1VfGT4n71RUF",
          "default_source": None,
          "default_tax_rates": [
          ],
          "description": None,
          "discount": None,
          "ended_at": None,
          "items": {
            "object": "list",
            "data": [
              {
                "id": "si_O1b0pRf6Zsr1K3",
                "object": "subscription_item",
                "billing_thresholds": None,
                "created": 1685949994,
                "metadata": {
                },
                "plan": {
                  "id": "price_1N8JnDBM2UVM1VfGDN6IsDDg",
                  "object": "plan",
                  "active": True,
                  "aggregate_usage": None,
                  "amount": 1000,
                  "amount_decimal": "1000",
                  "billing_scheme": "per_unit",
                  "created": 1684227819,
                  "currency": "usd",
                  "interval": "month",
                  "interval_count": 1,
                  "livemode": False,
                  "metadata": {
                  },
                  "nickname": None,
                  "product": "prod_Nu83RUXCw93YJs",
                  "tiers_mode": None,
                  "transform_usage": None,
                  "trial_period_days": 7,
                  "usage_type": "licensed"
                },
                "price": {
                  "id": "price_1N8JnDBM2UVM1VfGDN6IsDDg",
                  "object": "price",
                  "active": True,
                  "billing_scheme": "per_unit",
                  "created": 1684227819,
                  "currency": "usd",
                  "custom_unit_amount": None,
                  "livemode": False,
                  "lookup_key": None,
                  "metadata": {
                  },
                  "nickname": None,
                  "product": "prod_Nu83RUXCw93YJs",
                  "recurring": {
                    "aggregate_usage": None,
                    "interval": "month",
                    "interval_count": 1,
                    "trial_period_days": 7,
                    "usage_type": "licensed"
                  },
                  "tax_behavior": "unspecified",
                  "tiers_mode": None,
                  "transform_quantity": None,
                  "type": "recurring",
                  "unit_amount": 1000,
                  "unit_amount_decimal": "1000"
                },
                "quantity": 5,
                "subscription": "sub_1NFXoEBM2UVM1VfGmlBiJnqI",
                "tax_rates": [
                ]
              }
            ],
            "has_more": False,
            "total_count": 1,
            "url": "/v1/subscription_items?subscription=sub_1NFXoEiJnqI"
          },
          "latest_invoice": "in_1NFXoEBM2UVM1VfGpC9ydp1w",
          "livemode": False,
          "metadata": {
          },
          "next_pending_invoice_item_invoice": None,
          "on_behalf_of": None,
          "pause_collection": None,
          "payment_settings": {
            "payment_method_options": None,
            "payment_method_types": None,
            "save_default_payment_method": "off"
          },
          "pending_invoice_item_interval": None,
          "pending_setup_intent": None,
          "pending_update": None,
          "plan": {
            "id": "price_1N8JnDBM2UVM1VfGDN6IsDDg",
            "object": "plan",
            "active": True,
            "aggregate_usage": None,
            "amount": 1000,
            "amount_decimal": "1000",
            "billing_scheme": "per_unit",
            "created": 1684227819,
            "currency": "usd",
            "interval": "month",
            "interval_count": 1,
            "livemode": False,
            "metadata": {
            },
            "nickname": None,
            "product": "prod_Nu83RUXCw93YJs",
            "tiers_mode": None,
            "transform_usage": None,
            "trial_period_days": 7,
            "usage_type": "licensed"
          },
          "quantity": 5,
          "schedule": None,
          "start_date": 1685949994,
          "status": "trialing",
          "test_clock": None,
          "transfer_data": None,
          "trial_end": 1686121200,
          "trial_settings": {
            "end_behavior": {
              "missing_payment_method": "create_invoice"
            }
          },
          "trial_start": 1685949994
        },
        "previous_attributes": {
          "billing_cycle_anchor": 1686554794,
          "cancel_at": None,
          "canceled_at": None,
          "cancellation_details": {
            "reason": None
          },
          "current_period_end": 1686554794,
          "trial_end": 1686554794
        }
      },
      "livemode": False,
      "pending_webhooks": 1,
      "request": {
        "id": "req_FtfEvVazoAgQNy",
        "idempotency_key": "2c90d3c6-ce72-44cd-ba29-80c391629b82"
      },
      "type": "customer.subscription.updated"
    }
    event = stripe.Event.construct_from(
        values=data,
        key='!!@#'
    )
    customer_mock = mocker.Mock()
    subscription_mock = mocker.Mock()
    subscription_mock.customer = customer_mock
    get_subscription_by_id_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService._get_subscription_by_id',
        return_value=subscription_mock
    )
    get_valid_webhook_account_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService._get_valid_webhook_account_by_subs',
        return_value=account
    )
    subscription_details_mock = mocker.Mock()
    get_subscription_details_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService.get_subscription_details',
        return_value=subscription_details_mock
    )
    account_service_init_mock = mocker.patch.object(
        AccountSubscriptionService,
        attribute='__init__',
        return_value=None
    )
    account_service_update_mock = mocker.patch(
        'pneumatic_backend.payment.services.account.'
        'AccountSubscriptionService.update'
    )
    service = WebhookService()

    # act
    service._customer_subscription_updated(event)

    # assert
    get_subscription_by_id_mock.assert_called_once_with(subscription_stripe_id)
    get_valid_webhook_account_mock.assert_called_once_with(subscription_mock)
    get_subscription_details_mock.assert_called_once_with(subscription_mock)
    account_service_init_mock.assert_called_once_with(
        instance=account,
        user=user,
        auth_type=AuthTokenType.WEBHOOK
    )
    account_service_update_mock.assert_called_once_with(
        details=subscription_details_mock,
    )


def test_customer_subscription_updated__cancel__ok(mocker):

    customer_stripe_id = "cus_Nx9XuHa4xteob3"
    account = create_test_account(stripe_id=customer_stripe_id)
    user = create_test_user(account=account)
    subscription_stripe_id = 'sub_1NG6tmBM2UVM1VfG3Gnat77h'
    cancel_at = timezone.now() + timedelta(days=5)
    cancel_at_timestamp = cancel_at.timestamp()

    data = {
      "id": "evt_1NG6HSBM2UVM1VfG5ChrCp3O",
      "object": "event",
      "api_version": "2022-11-15",
      "created": 1686082502,
      "data": {
        "object": {
          "id": subscription_stripe_id,
          "object": "subscription",
          "application": None,
          "application_fee_percent": None,
          "automatic_tax": {
            "enabled": False
          },
          "billing_cycle_anchor": 1686121200,
          "billing_thresholds": None,
          "cancel_at": cancel_at_timestamp,
          "cancel_at_period_end": False,
          "canceled_at": 1686082502,
          "cancellation_details": {
            "comment": None,
            "feedback": None,
            "reason": "cancellation_requested"
          },
          "collection_method": "charge_automatically",
          "created": 1685949994,
          "currency": "usd",
          "current_period_end": 1686121200,
          "current_period_start": 1685949994,
          "customer": "cus_O1ax86Phph0xyw",
          "days_until_due": None,
          "default_payment_method": "pm_1NFXoCBM2UVM1VfGT4n71RUF",
          "default_source": None,
          "default_tax_rates": [
          ],
          "description": None,
          "discount": None,
          "ended_at": None,
          "items": {
            "object": "list",
            "data": [
              {
                "id": "si_O1b0pRf6Zsr1K3",
                "object": "subscription_item",
                "billing_thresholds": None,
                "created": 1685949994,
                "metadata": {
                },
                "plan": {
                  "id": "price_1N8JnDBM2UVM1VfGDN6IsDDg",
                  "object": "plan",
                  "active": True,
                  "aggregate_usage": None,
                  "amount": 1000,
                  "amount_decimal": "1000",
                  "billing_scheme": "per_unit",
                  "created": 1684227819,
                  "currency": "usd",
                  "interval": "month",
                  "interval_count": 1,
                  "livemode": False,
                  "metadata": {
                  },
                  "nickname": None,
                  "product": "prod_Nu83RUXCw93YJs",
                  "tiers_mode": None,
                  "transform_usage": None,
                  "trial_period_days": 7,
                  "usage_type": "licensed"
                },
                "price": {
                  "id": "price_1N8JnDBM2UVM1VfGDN6IsDDg",
                  "object": "price",
                  "active": True,
                  "billing_scheme": "per_unit",
                  "created": 1684227819,
                  "currency": "usd",
                  "custom_unit_amount": None,
                  "livemode": False,
                  "lookup_key": None,
                  "metadata": {
                  },
                  "nickname": None,
                  "product": "prod_Nu83RUXCw93YJs",
                  "recurring": {
                    "aggregate_usage": None,
                    "interval": "month",
                    "interval_count": 1,
                    "trial_period_days": 7,
                    "usage_type": "licensed"
                  },
                  "tax_behavior": "unspecified",
                  "tiers_mode": None,
                  "transform_quantity": None,
                  "type": "recurring",
                  "unit_amount": 1000,
                  "unit_amount_decimal": "1000"
                },
                "quantity": 5,
                "subscription": "sub_1NFXoEBM2UVM1VfGmlBiJnqI",
                "tax_rates": [
                ]
              }
            ],
            "has_more": False,
            "total_count": 1,
            "url": "/v1/subscription_items?subscription=sub_1NFXoEiJnqI"
          },
          "latest_invoice": "in_1NFXoEBM2UVM1VfGpC9ydp1w",
          "livemode": False,
          "metadata": {
          },
          "next_pending_invoice_item_invoice": None,
          "on_behalf_of": None,
          "pause_collection": None,
          "payment_settings": {
            "payment_method_options": None,
            "payment_method_types": None,
            "save_default_payment_method": "off"
          },
          "pending_invoice_item_interval": None,
          "pending_setup_intent": None,
          "pending_update": None,
          "plan": {
            "id": "price_1N8JnDBM2UVM1VfGDN6IsDDg",
            "object": "plan",
            "active": True,
            "aggregate_usage": None,
            "amount": 1000,
            "amount_decimal": "1000",
            "billing_scheme": "per_unit",
            "created": 1684227819,
            "currency": "usd",
            "interval": "month",
            "interval_count": 1,
            "livemode": False,
            "metadata": {
            },
            "nickname": None,
            "product": "prod_Nu83RUXCw93YJs",
            "tiers_mode": None,
            "transform_usage": None,
            "trial_period_days": 7,
            "usage_type": "licensed"
          },
          "quantity": 5,
          "schedule": None,
          "start_date": 1685949994,
          "status": "trialing",
          "test_clock": None,
          "transfer_data": None,
          "trial_end": 1686121200,
          "trial_settings": {
            "end_behavior": {
              "missing_payment_method": "create_invoice"
            }
          },
          "trial_start": 1685949994
        },
        "previous_attributes": {
          "billing_cycle_anchor": 1686554794,
          "cancel_at": None,
          "canceled_at": None,
          "cancellation_details": {
            "reason": None
          },
          "current_period_end": 1686554794,
          "trial_end": 1686554794
        }
      },
      "livemode": False,
      "pending_webhooks": 1,
      "request": {
        "id": "req_FtfEvVazoAgQNy",
        "idempotency_key": "2c90d3c6-ce72-44cd-ba29-80c391629b82"
      },
      "type": "customer.subscription.updated"
    }
    event = stripe.Event.construct_from(
        values=data,
        key='!!@#'
    )
    customer_mock = mocker.Mock()
    subscription_mock = mocker.Mock()
    subscription_mock.customer = customer_mock
    get_subscription_by_id_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService._get_subscription_by_id',
        return_value=subscription_mock
    )
    get_valid_webhook_account_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService._get_valid_webhook_account_by_subs',
        return_value=account
    )
    get_subscription_details_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService.get_subscription_details',
    )
    account_service_init_mock = mocker.patch.object(
        AccountSubscriptionService,
        attribute='__init__',
        return_value=None
    )
    account_service_update_mock = mocker.patch(
        'pneumatic_backend.payment.services.account.'
        'AccountSubscriptionService.update'
    )
    account_service_cancel_mock = mocker.patch(
        'pneumatic_backend.payment.services.account.'
        'AccountSubscriptionService.cancel'
    )
    service = WebhookService()

    # act
    service._customer_subscription_updated(event)

    # assert
    get_subscription_by_id_mock.assert_called_once_with(subscription_stripe_id)
    get_valid_webhook_account_mock.assert_called_once_with(subscription_mock)
    account_service_init_mock.assert_called_once_with(
        instance=account,
        user=user,
        auth_type=AuthTokenType.WEBHOOK
    )
    account_service_cancel_mock.assert_called_once_with(cancel_at)
    get_subscription_details_mock.assert_not_called()
    account_service_update_mock.assert_not_called()


def test_customer_subscription_updated__tenant__update__ok(mocker):

    # arrange
    customer_stripe_id = "cus_Nx9XuHa4xteob3"
    master_account = create_test_account(stripe_id=customer_stripe_id)
    create_test_user(account=master_account)
    tenant = create_test_account(
        name='Tenant',
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    tenant_owner = create_test_user(
        account=tenant,
        is_account_owner=True,
        email='tenant@owner.com'
    )

    subscription_stripe_id = 'sub_1NG6tmBM2UVM1VfG3Gnat77h'
    cancel_at = None
    data = {
      "id": "evt_1NG6HSBM2UVM1VfG5ChrCp3O",
      "object": "event",
      "api_version": "2022-11-15",
      "created": 1686082502,
      "data": {
        "object": {
          "id": subscription_stripe_id,
          "object": "subscription",
          "application": None,
          "application_fee_percent": None,
          "automatic_tax": {
            "enabled": False
          },
          "billing_cycle_anchor": 1686121200,
          "billing_thresholds": None,
          "cancel_at": cancel_at,
          "cancel_at_period_end": False,
          "canceled_at": 1686082502,
          "cancellation_details": {
            "comment": None,
            "feedback": None,
            "reason": "cancellation_requested"
          },
          "collection_method": "charge_automatically",
          "created": 1685949994,
          "currency": "usd",
          "current_period_end": 1686121200,
          "current_period_start": 1685949994,
          "customer": "cus_O1ax86Phph0xyw",
          "days_until_due": None,
          "default_payment_method": "pm_1NFXoCBM2UVM1VfGT4n71RUF",
          "default_source": None,
          "default_tax_rates": [
          ],
          "description": None,
          "discount": None,
          "ended_at": None,
          "items": {
            "object": "list",
            "data": [
              {
                "id": "si_O1b0pRf6Zsr1K3",
                "object": "subscription_item",
                "billing_thresholds": None,
                "created": 1685949994,
                "metadata": {
                },
                "plan": {
                  "id": "price_1N8JnDBM2UVM1VfGDN6IsDDg",
                  "object": "plan",
                  "active": True,
                  "aggregate_usage": None,
                  "amount": 1000,
                  "amount_decimal": "1000",
                  "billing_scheme": "per_unit",
                  "created": 1684227819,
                  "currency": "usd",
                  "interval": "month",
                  "interval_count": 1,
                  "livemode": False,
                  "metadata": {
                  },
                  "nickname": None,
                  "product": "prod_Nu83RUXCw93YJs",
                  "tiers_mode": None,
                  "transform_usage": None,
                  "trial_period_days": 7,
                  "usage_type": "licensed"
                },
                "price": {
                  "id": "price_1N8JnDBM2UVM1VfGDN6IsDDg",
                  "object": "price",
                  "active": True,
                  "billing_scheme": "per_unit",
                  "created": 1684227819,
                  "currency": "usd",
                  "custom_unit_amount": None,
                  "livemode": False,
                  "lookup_key": None,
                  "metadata": {
                  },
                  "nickname": None,
                  "product": "prod_Nu83RUXCw93YJs",
                  "recurring": {
                    "aggregate_usage": None,
                    "interval": "month",
                    "interval_count": 1,
                    "trial_period_days": 7,
                    "usage_type": "licensed"
                  },
                  "tax_behavior": "unspecified",
                  "tiers_mode": None,
                  "transform_quantity": None,
                  "type": "recurring",
                  "unit_amount": 1000,
                  "unit_amount_decimal": "1000"
                },
                "quantity": 5,
                "subscription": "sub_1NFXoEBM2UVM1VfGmlBiJnqI",
                "tax_rates": [
                ]
              }
            ],
            "has_more": False,
            "total_count": 1,
            "url": "/v1/subscription_items?subscription=sub_1NFXoEiJnqI"
          },
          "latest_invoice": "in_1NFXoEBM2UVM1VfGpC9ydp1w",
          "livemode": False,
          "metadata": {
          },
          "next_pending_invoice_item_invoice": None,
          "on_behalf_of": None,
          "pause_collection": None,
          "payment_settings": {
            "payment_method_options": None,
            "payment_method_types": None,
            "save_default_payment_method": "off"
          },
          "pending_invoice_item_interval": None,
          "pending_setup_intent": None,
          "pending_update": None,
          "plan": {
            "id": "price_1N8JnDBM2UVM1VfGDN6IsDDg",
            "object": "plan",
            "active": True,
            "aggregate_usage": None,
            "amount": 1000,
            "amount_decimal": "1000",
            "billing_scheme": "per_unit",
            "created": 1684227819,
            "currency": "usd",
            "interval": "month",
            "interval_count": 1,
            "livemode": False,
            "metadata": {
            },
            "nickname": None,
            "product": "prod_Nu83RUXCw93YJs",
            "tiers_mode": None,
            "transform_usage": None,
            "trial_period_days": 7,
            "usage_type": "licensed"
          },
          "quantity": 5,
          "schedule": None,
          "start_date": 1685949994,
          "status": "trialing",
          "test_clock": None,
          "transfer_data": None,
          "trial_end": 1686121200,
          "trial_settings": {
            "end_behavior": {
              "missing_payment_method": "create_invoice"
            }
          },
          "trial_start": 1685949994
        },
        "previous_attributes": {
          "billing_cycle_anchor": 1686554794,
          "cancel_at": None,
          "canceled_at": None,
          "cancellation_details": {
            "reason": None
          },
          "current_period_end": 1686554794,
          "trial_end": 1686554794
        }
      },
      "livemode": False,
      "pending_webhooks": 1,
      "request": {
        "id": "req_FtfEvVazoAgQNy",
        "idempotency_key": "2c90d3c6-ce72-44cd-ba29-80c391629b82"
      },
      "type": "customer.subscription.updated"
    }
    event = stripe.Event.construct_from(
        values=data,
        key='!!@#'
    )
    customer_mock = mocker.Mock()
    subscription_mock = mocker.Mock()
    subscription_mock.customer = customer_mock
    get_subscription_by_id_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService._get_subscription_by_id',
        return_value=subscription_mock
    )
    get_valid_webhook_account_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService._get_valid_webhook_account_by_subs',
        return_value=tenant
    )
    subscription_details_mock = mocker.Mock()
    get_subscription_details_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService.get_subscription_details',
        return_value=subscription_details_mock
    )
    account_service_init_mock = mocker.patch.object(
        AccountSubscriptionService,
        attribute='__init__',
        return_value=None
    )
    account_service_update_mock = mocker.patch(
        'pneumatic_backend.payment.services.account.'
        'AccountSubscriptionService.update'
    )
    service = WebhookService()

    # act
    service._customer_subscription_updated(event)

    # assert
    get_subscription_by_id_mock.assert_called_once_with(subscription_stripe_id)
    get_valid_webhook_account_mock.assert_called_once_with(subscription_mock)
    get_subscription_details_mock.assert_called_once_with(subscription_mock)
    account_service_init_mock.assert_called_once_with(
        instance=tenant,
        user=tenant_owner,
        auth_type=AuthTokenType.WEBHOOK
    )
    account_service_update_mock.assert_called_once_with(
        details=subscription_details_mock,
    )


def test_customer_subscription_deleted__ok(mocker):

    # arrange
    customer_stripe_id = "cus_Nx9XuHa4xteob3"
    account = create_test_account(stripe_id=customer_stripe_id)
    user = create_test_user(account=account)
    subscription_stripe_id = 'sub_1NG6tmBM2UVM1VfG3Gnat77h'
    ended_at = timezone.now() + timedelta(days=5)
    ended_at_timestamp = ended_at.timestamp()
    data = {
      "id": "evt_1NG597BM2UVM1VfGi5bQXbq8",
      "object": "event",
      "api_version": "2022-11-15",
      "created": 1686078141,
      "data": {
        "object": {
          "id": subscription_stripe_id,
          "object": "subscription",
          "application": None,
          "application_fee_percent": None,
          "automatic_tax": {
            "enabled": False
          },
          "billing_cycle_anchor": 1686339894,
          "billing_thresholds": None,
          "cancel_at": None,
          "cancel_at_period_end": False,
          "canceled_at": 1686078141,
          "cancellation_details": {
            "comment": None,
            "feedback": None,
            "reason": "cancellation_requested"
          },
          "collection_method": "charge_automatically",
          "created": 1685735094,
          "currency": "usd",
          "current_period_end": 1686339894,
          "current_period_start": 1685735094,
          "customer": "cus_O0fEs0yla8FC7T",
          "days_until_due": None,
          "default_payment_method": "pm_1NEdupBM2UVM1VfGcLhwnS9m",
          "default_source": None,
          "default_tax_rates": [
          ],
          "description": None,
          "discount": None,
          "ended_at": ended_at_timestamp,
          "items": {
            "object": "list",
            "data": [
              {
                "id": "si_O0fEdfplY7M7oh",
                "object": "subscription_item",
                "billing_thresholds": None,
                "created": 1685735095,
                "metadata": {
                },
                "plan": {
                  "id": "price_1N8JnDBM2UVM1VfGDN6IsDDg",
                  "object": "plan",
                  "active": True,
                  "aggregate_usage": None,
                  "amount": 1000,
                  "amount_decimal": "1000",
                  "billing_scheme": "per_unit",
                  "created": 1684227819,
                  "currency": "usd",
                  "interval": "month",
                  "interval_count": 1,
                  "livemode": False,
                  "metadata": {
                  },
                  "nickname": None,
                  "product": "prod_Nu83RUXCw93YJs",
                  "tiers_mode": None,
                  "transform_usage": None,
                  "trial_period_days": 7,
                  "usage_type": "licensed"
                },
                "price": {
                  "id": "price_1N8JnDBM2UVM1VfGDN6IsDDg",
                  "object": "price",
                  "active": True,
                  "billing_scheme": "per_unit",
                  "created": 1684227819,
                  "currency": "usd",
                  "custom_unit_amount": None,
                  "livemode": False,
                  "lookup_key": None,
                  "metadata": {
                  },
                  "nickname": None,
                  "product": "prod_Nu83RUXCw93YJs",
                  "recurring": {
                    "aggregate_usage": None,
                    "interval": "month",
                    "interval_count": 1,
                    "trial_period_days": 7,
                    "usage_type": "licensed"
                  },
                  "tax_behavior": "unspecified",
                  "tiers_mode": None,
                  "transform_quantity": None,
                  "type": "recurring",
                  "unit_amount": 1000,
                  "unit_amount_decimal": "1000"
                },
                "quantity": 5,
                "subscription": "sub_1NEdu6BM2UVM1VfG6s72BJVo",
                "tax_rates": [
                ]
              }
            ],
            "has_more": False,
            "total_count": 1,
            "url": "/v1/subscription_items?subscription=sub_1NEdG6s72BJVo"
          },
          "latest_invoice": "in_1NEdu6BM2UVM1VfGW5ceYbF5",
          "livemode": False,
          "metadata": {
          },
          "next_pending_invoice_item_invoice": None,
          "on_behalf_of": None,
          "pause_collection": None,
          "payment_settings": {
            "payment_method_options": None,
            "payment_method_types": None,
            "save_default_payment_method": "off"
          },
          "pending_invoice_item_interval": None,
          "pending_setup_intent": None,
          "pending_update": None,
          "plan": {
            "id": "price_1N8JnDBM2UVM1VfGDN6IsDDg",
            "object": "plan",
            "active": True,
            "aggregate_usage": None,
            "amount": 1000,
            "amount_decimal": "1000",
            "billing_scheme": "per_unit",
            "created": 1684227819,
            "currency": "usd",
            "interval": "month",
            "interval_count": 1,
            "livemode": False,
            "metadata": {
            },
            "nickname": None,
            "product": "prod_Nu83RUXCw93YJs",
            "tiers_mode": None,
            "transform_usage": None,
            "trial_period_days": 7,
            "usage_type": "licensed"
          },
          "quantity": 5,
          "schedule": None,
          "start_date": 1685735094,
          "status": "canceled",
          "test_clock": None,
          "transfer_data": None,
          "trial_end": 1686339894,
          "trial_settings": {
            "end_behavior": {
              "missing_payment_method": "create_invoice"
            }
          },
          "trial_start": 1685735094
        }
      },
      "livemode": False,
      "pending_webhooks": 1,
      "request": {
        "id": "req_Wba3rJCrwj7mdX",
        "idempotency_key": None
      },
      "type": "customer.subscription.deleted"
    }
    event = stripe.Event.construct_from(
        values=data,
        key='!!@#'
    )
    customer_mock = mocker.Mock()
    subscription_mock = mocker.Mock()
    subscription_mock.customer = customer_mock
    get_subscription_by_id_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService._get_subscription_by_id',
        return_value=subscription_mock
    )
    get_valid_webhook_account_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService._get_valid_webhook_account_by_subs',
        return_value=account
    )
    account_service_init_mock = mocker.patch.object(
        AccountSubscriptionService,
        attribute='__init__',
        return_value=None
    )
    account_service_expired_mock = mocker.patch(
        'pneumatic_backend.payment.services.account.'
        'AccountSubscriptionService.expired'
    )
    service = WebhookService()

    # act
    service._customer_subscription_deleted(event)

    # assert
    get_subscription_by_id_mock.assert_called_once_with(subscription_stripe_id)
    get_valid_webhook_account_mock.assert_called_once_with(subscription_mock)
    account_service_init_mock.assert_called_once_with(
        instance=account,
        user=user,
        auth_type=AuthTokenType.WEBHOOK
    )
    account_service_expired_mock.assert_called_once_with(ended_at)


def test_customer_subscription_deleted__tenant__ok(mocker):

    # arrange
    customer_stripe_id = "cus_Nx9XuHa4xteob3"
    master_account = create_test_account(stripe_id=customer_stripe_id)
    create_test_user(account=master_account)
    tenant = create_test_account(
        name='Tenant',
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    tenant_owner = create_test_user(
        account=tenant,
        is_account_owner=True,
        email='tenant@owner.com'
    )

    subscription_stripe_id = 'sub_1NG6tmBM2UVM1VfG3Gnat77h'
    ended_at = timezone.now() + timedelta(days=5)
    ended_at_timestamp = ended_at.timestamp()
    data = {
      "id": "evt_1NG597BM2UVM1VfGi5bQXbq8",
      "object": "event",
      "api_version": "2022-11-15",
      "created": 1686078141,
      "data": {
        "object": {
          "id": subscription_stripe_id,
          "object": "subscription",
          "application": None,
          "application_fee_percent": None,
          "automatic_tax": {
            "enabled": False
          },
          "billing_cycle_anchor": 1686339894,
          "billing_thresholds": None,
          "cancel_at": None,
          "cancel_at_period_end": False,
          "canceled_at": 1686078141,
          "cancellation_details": {
            "comment": None,
            "feedback": None,
            "reason": "cancellation_requested"
          },
          "collection_method": "charge_automatically",
          "created": 1685735094,
          "currency": "usd",
          "current_period_end": 1686339894,
          "current_period_start": 1685735094,
          "customer": "cus_O0fEs0yla8FC7T",
          "days_until_due": None,
          "default_payment_method": "pm_1NEdupBM2UVM1VfGcLhwnS9m",
          "default_source": None,
          "default_tax_rates": [
          ],
          "description": None,
          "discount": None,
          "ended_at": ended_at_timestamp,
          "items": {
            "object": "list",
            "data": [
              {
                "id": "si_O0fEdfplY7M7oh",
                "object": "subscription_item",
                "billing_thresholds": None,
                "created": 1685735095,
                "metadata": {
                },
                "plan": {
                  "id": "price_1N8JnDBM2UVM1VfGDN6IsDDg",
                  "object": "plan",
                  "active": True,
                  "aggregate_usage": None,
                  "amount": 1000,
                  "amount_decimal": "1000",
                  "billing_scheme": "per_unit",
                  "created": 1684227819,
                  "currency": "usd",
                  "interval": "month",
                  "interval_count": 1,
                  "livemode": False,
                  "metadata": {
                  },
                  "nickname": None,
                  "product": "prod_Nu83RUXCw93YJs",
                  "tiers_mode": None,
                  "transform_usage": None,
                  "trial_period_days": 7,
                  "usage_type": "licensed"
                },
                "price": {
                  "id": "price_1N8JnDBM2UVM1VfGDN6IsDDg",
                  "object": "price",
                  "active": True,
                  "billing_scheme": "per_unit",
                  "created": 1684227819,
                  "currency": "usd",
                  "custom_unit_amount": None,
                  "livemode": False,
                  "lookup_key": None,
                  "metadata": {
                  },
                  "nickname": None,
                  "product": "prod_Nu83RUXCw93YJs",
                  "recurring": {
                    "aggregate_usage": None,
                    "interval": "month",
                    "interval_count": 1,
                    "trial_period_days": 7,
                    "usage_type": "licensed"
                  },
                  "tax_behavior": "unspecified",
                  "tiers_mode": None,
                  "transform_quantity": None,
                  "type": "recurring",
                  "unit_amount": 1000,
                  "unit_amount_decimal": "1000"
                },
                "quantity": 5,
                "subscription": "sub_1NEdu6BM2UVM1VfG6s72BJVo",
                "tax_rates": [
                ]
              }
            ],
            "has_more": False,
            "total_count": 1,
            "url": "/v1/subscription_items?subscription=sub_1NEdG6s72BJVo"
          },
          "latest_invoice": "in_1NEdu6BM2UVM1VfGW5ceYbF5",
          "livemode": False,
          "metadata": {
          },
          "next_pending_invoice_item_invoice": None,
          "on_behalf_of": None,
          "pause_collection": None,
          "payment_settings": {
            "payment_method_options": None,
            "payment_method_types": None,
            "save_default_payment_method": "off"
          },
          "pending_invoice_item_interval": None,
          "pending_setup_intent": None,
          "pending_update": None,
          "plan": {
            "id": "price_1N8JnDBM2UVM1VfGDN6IsDDg",
            "object": "plan",
            "active": True,
            "aggregate_usage": None,
            "amount": 1000,
            "amount_decimal": "1000",
            "billing_scheme": "per_unit",
            "created": 1684227819,
            "currency": "usd",
            "interval": "month",
            "interval_count": 1,
            "livemode": False,
            "metadata": {
            },
            "nickname": None,
            "product": "prod_Nu83RUXCw93YJs",
            "tiers_mode": None,
            "transform_usage": None,
            "trial_period_days": 7,
            "usage_type": "licensed"
          },
          "quantity": 5,
          "schedule": None,
          "start_date": 1685735094,
          "status": "canceled",
          "test_clock": None,
          "transfer_data": None,
          "trial_end": 1686339894,
          "trial_settings": {
            "end_behavior": {
              "missing_payment_method": "create_invoice"
            }
          },
          "trial_start": 1685735094
        }
      },
      "livemode": False,
      "pending_webhooks": 1,
      "request": {
        "id": "req_Wba3rJCrwj7mdX",
        "idempotency_key": None
      },
      "type": "customer.subscription.deleted"
    }
    event = stripe.Event.construct_from(
        values=data,
        key='!!@#'
    )
    customer_mock = mocker.Mock()
    subscription_mock = mocker.Mock()
    subscription_mock.customer = customer_mock
    get_subscription_by_id_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService._get_subscription_by_id',
        return_value=subscription_mock
    )
    get_valid_webhook_account_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService._get_valid_webhook_account_by_subs',
        return_value=tenant
    )
    account_service_init_mock = mocker.patch.object(
        AccountSubscriptionService,
        attribute='__init__',
        return_value=None
    )
    account_service_expired_mock = mocker.patch(
        'pneumatic_backend.payment.services.account.'
        'AccountSubscriptionService.expired'
    )
    service = WebhookService()

    # act
    service._customer_subscription_deleted(event)

    # assert
    get_subscription_by_id_mock.assert_called_once_with(subscription_stripe_id)
    get_valid_webhook_account_mock.assert_called_once_with(subscription_mock)
    account_service_init_mock.assert_called_once_with(
        instance=tenant,
        user=tenant_owner,
        auth_type=AuthTokenType.WEBHOOK
    )
    account_service_expired_mock.assert_called_once_with(ended_at)


def test_product_created__ok(mocker):

    # arrange
    stripe_id = "prod_O2DByEkAsBnjUC"
    name = "New product"
    is_active = True
    data = {
      "id": "evt_1NG8l0BM2UVM1VfGnEoweMsp",
      "object": "event",
      "api_version": "2022-11-15",
      "created": 1686092022,
      "data": {
        "object": {
          "id": stripe_id,
          "object": "product",
          "active": is_active,
          "attributes": [
          ],
          "created": 1686092022,
          "default_price": None,
          "description": None,
          "images": [
          ],
          "livemode": False,
          "metadata": {
          },
          "name": name,
          "package_dimensions": None,
          "shippable": None,
          "statement_descriptor": None,
          "tax_code": None,
          "type": "service",
          "unit_label": None,
          "updated": 1686092022,
          "url": None
        }
      },
      "livemode": False,
      "pending_webhooks": 1,
      "request": {
        "id": "req_y1g0sf9xfEl4uv",
        "idempotency_key": "0d8ee425-6445-425d-8521-fdd46b6fe4c4"
      },
      "type": "product.created"
    }
    event = stripe.Event.construct_from(
        values=data,
        key='!!@#'
    )
    product_code = 'some code'
    get_product_code_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService._get_product_code',
        return_value=product_code
    )
    service = WebhookService()

    # act
    service._product_created(event)

    # assert
    assert Product.objects.filter(
        name=name,
        stripe_id=stripe_id,
        is_active=is_active,
        code=product_code,
    ).exists()
    get_product_code_mock.assert_called_once_with(
        stripe_id=stripe_id,
        name=name
    )


def test_product_updated__ok():

    # arrange
    stripe_id = "prod_O2DByEkAsBnjUC"
    name = "New product"
    is_active = True

    data = {
      "id": "evt_1NG8XBBM2UVM1VfGk3fEtGm4",
      "object": "event",
      "api_version": "2022-11-15",
      "created": 1686091165,
      "data": {
        "object": {
          "id": stripe_id,
          "object": "product",
          "active": is_active,
          "attributes": [
          ],
          "created": 1684227818,
          "default_price": "price_1N8JnDBM2UVM1VfGDN6IsDDg",
          "description": "Advanced features for growing team 1",
          "images": [
          ],
          "livemode": False,
          "metadata": {
          },
          "name": name,
          "package_dimensions": None,
          "shippable": None,
          "statement_descriptor": None,
          "tax_code": None,
          "type": "service",
          "unit_label": None,
          "updated": 1686091165,
          "url": None
        },
        "previous_attributes": {
          "updated": 1686091164
        }
      },
      "livemode": False,
      "pending_webhooks": 1,
      "request": {
        "id": "req_Dd4K0wIP5khFtA",
        "idempotency_key": "7bebe648-6102-4988-85f3-f33cbf8f731d"
      },
      "type": "product.updated"
    }
    event = stripe.Event.construct_from(
        values=data,
        key='!!@#'
    )
    code = 'some code'
    product = create_test_product(stripe_id=stripe_id, code=code)
    service = WebhookService()

    # act
    service._product_updated(event)

    # assert
    product.refresh_from_db()
    assert product.code == code
    assert product.name == name
    assert product.stripe_id == stripe_id
    assert product.is_active == is_active


def test_product_deleted():

    # arrange
    stripe_id = "prod_O2DByEkAsBnjUC"
    data = {
      "id": "evt_1NG8n1BM2UVM1VfGLv20Skzf",
      "object": "event",
      "api_version": "2022-11-15",
      "created": 1686092147,
      "data": {
        "object": {
          "id": stripe_id,
          "object": "product",
          "active": False,
          "attributes": [
          ],
          "created": 1686092022,
          "default_price": None,
          "description": None,
          "images": [
          ],
          "livemode": False,
          "metadata": {
          },
          "name": "1",
          "package_dimensions": None,
          "shippable": None,
          "statement_descriptor": None,
          "tax_code": None,
          "type": "service",
          "unit_label": None,
          "updated": 1686092147,
          "url": None
        }
      },
      "livemode": False,
      "pending_webhooks": 1,
      "request": {
        "id": "req_oxf7W64DISLKeL",
        "idempotency_key": None
      },
      "type": "product.deleted"
    }
    event = stripe.Event.construct_from(
        values=data,
        key='!!@#'
    )
    product = create_test_product(stripe_id=stripe_id)
    create_test_recurring_price(product=product)

    service = WebhookService()

    # act
    service._product_deleted(event)

    # assert
    assert not Product.objects.filter(stripe_id=stripe_id).exists()
    assert not Price.objects.filter(product__stripe_id=stripe_id).exists()


def test_price_created__ok(mocker):

    # arrange
    data = {
      "id": "evt_1NG8l0BM2UVM1VfGZo5GSCLu",
      "object": "event",
      "api_version": "2022-11-15",
      "created": 1686092022,
      "data": {
        "object": {
          "id": 'price_1NG8l0BM2UVM1VfGAlpUVQ5k',
          "object": "price",
          "active": True,
          "billing_scheme": "per_unit",
          "created": 1686092022,
          "currency": 'usd',
          "custom_unit_amount": None,
          "livemode": False,
          "lookup_key": None,
          "metadata": {
          },
          "nickname": None,
          "product": 'pr_123',
          "recurring": {
            "aggregate_usage": None,
            "interval": 'year',
            "interval_count": 1,
            "trial_period_days": 5,
            "usage_type": "licensed"
          },
          "tax_behavior": "unspecified",
          "tiers_mode": None,
          "transform_quantity": None,
          "type": 'recurring',
          "unit_amount": 1000,
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
    create_price_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService._create_price'
    )
    service = WebhookService()

    # act
    service._price_created(event)

    # assert
    create_price_mock.assert_called_once_with(
        event.data['object']
    )


def test_price_updated__recurring__ok():

    # arrange
    product = create_test_product()
    stripe_id = 'price_1NG8l0BM2UVM1VfGAlpUVQ5k'
    is_active = False
    interval = BillingPeriod.DAILY
    unit_amount = 100
    trial_days = 5
    currency = 'eur'
    price_code = 'some code'
    price = create_test_recurring_price(
        stripe_id=stripe_id,
        product=product,
        code=price_code
    )
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
      "type": "price.updated"
    }
    event = stripe.Event.construct_from(
        values=data,
        key='!!@#'
    )
    service = WebhookService()

    # act
    service._price_updated(event)

    # assert
    price.refresh_from_db()
    assert price.product == product
    assert price.status == PriceStatus.INACTIVE
    assert price.name == 'Premium day'
    assert price.code == price_code
    assert price.stripe_id == stripe_id
    assert price.price_type == PriceType.RECURRING
    assert price.price == unit_amount
    assert price.trial_days == trial_days
    assert price.billing_period == interval
    assert price.currency == currency


def test_price_updated__one_time__ok():

    # arrange
    product = create_test_product()
    stripe_id = 'price_1NG8l0BM2UVM1VfGAlpUVQ5k'
    is_active = True
    unit_amount = 1000
    currency = 'usd'
    price = create_test_invoice_price(stripe_id=stripe_id, product=product)
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
      "type": "price.update"
    }
    event = stripe.Event.construct_from(
        values=data,
        key='!!@#'
    )
    service = WebhookService()

    # act
    service._price_updated(event)

    # assert
    assert Price.objects.filter(
        id=price.id,
        product=product,
        # status=PriceStatus.ACTIVE,
        name='Premium',
        code=price.code,
        stripe_id=stripe_id,
        price_type=PriceType.ONE_TIME,
        price=unit_amount,
        trial_days=None,
        billing_period=None,
        currency=currency
    ).exists()


def test_price_updated__archived_to_active__archived():

    # arrange
    product = create_test_product()
    stripe_id = 'price_1NG8l0BM2UVM1VfGAlpUVQ5k'
    is_active = True
    interval = BillingPeriod.DAILY
    unit_amount = 100
    trial_days = 5
    currency = 'eur'
    price_code = 'some code'
    price = create_test_recurring_price(
        stripe_id=stripe_id,
        product=product,
        code=price_code,
        status=PriceStatus.ARCHIVED,
    )
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
      "type": "price.updated"
    }
    event = stripe.Event.construct_from(
        values=data,
        key='!!@#'
    )
    service = WebhookService()

    # act
    service._price_updated(event)

    # assert
    price.refresh_from_db()
    assert price.product == product
    assert price.status == PriceStatus.ARCHIVED
    assert price.name == 'Premium day'


def test_price_updated__archived_to_inactive__ok():

    # arrange
    product = create_test_product()
    stripe_id = 'price_1NG8l0BM2UVM1VfGAlpUVQ5k'
    is_active = False
    interval = BillingPeriod.DAILY
    unit_amount = 100
    trial_days = 5
    currency = 'eur'
    price_code = 'some code'
    price = create_test_recurring_price(
        stripe_id=stripe_id,
        product=product,
        code=price_code,
        status=PriceStatus.ARCHIVED,
    )
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
      "type": "price.updated"
    }
    event = stripe.Event.construct_from(
        values=data,
        key='!!@#'
    )
    service = WebhookService()

    # act
    service._price_updated(event)

    # assert
    price.refresh_from_db()
    assert price.product == product
    assert price.status == PriceStatus.INACTIVE
    assert price.name == 'Premium day'


def test_price_deleted():

    # arrange
    stripe_id = "prod_O2DByEkAsBnjUC"
    data = {
      "id": "evt_1NG8n1BM2UVM1VfGLv20Skzf",
      "object": "event",
      "api_version": "2022-11-15",
      "created": 1686092147,
      "data": {
        "object": {
          "id": stripe_id,
          "object": "product",
          "active": False,
          "attributes": [
          ],
          "created": 1686092022,
          "default_price": None,
          "description": None,
          "images": [
          ],
          "livemode": False,
          "metadata": {
          },
          "name": "1",
          "package_dimensions": None,
          "shippable": None,
          "statement_descriptor": None,
          "tax_code": None,
          "type": "service",
          "unit_label": None,
          "updated": 1686092147,
          "url": None
        }
      },
      "livemode": False,
      "pending_webhooks": 1,
      "request": {
        "id": "req_oxf7W64DISLKeL",
        "idempotency_key": None
      },
      "type": "product.deleted"
    }
    event = stripe.Event.construct_from(
        values=data,
        key='!!@#'
    )
    create_test_recurring_price(stripe_id=stripe_id)

    service = WebhookService()

    # act
    service._price_deleted(event)

    # assert
    assert not Price.objects.filter(stripe_id=stripe_id).exists()


def test_handle__handler_exist__ok(mocker):

    # arrange
    stripe_id = "prod_O2DByEkAsBnjUC"
    data = {
      "id": "evt_1NG8n1BM2UVM1VfGLv20Skzf",
      "object": "event",
      "api_version": "2022-11-15",
      "created": 1686092147,
      "data": {
        "object": {
          "id": stripe_id,
          "object": "product",
          "active": False,
          "attributes": [
          ],
          "created": 1686092022,
          "default_price": None,
          "description": None,
          "images": [
          ],
          "livemode": False,
          "metadata": {
          },
          "name": "1",
          "package_dimensions": None,
          "shippable": None,
          "statement_descriptor": None,
          "tax_code": None,
          "type": "service",
          "unit_label": None,
          "updated": 1686092147,
          "url": None
        }
      },
      "livemode": False,
      "pending_webhooks": 1,
      "request": {
        "id": "req_oxf7W64DISLKeL",
        "idempotency_key": None
      },
      "type": "product.deleted"
    }
    handler_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.WebhookService'
        '._product_deleted'
    )
    key = '!@#d'
    event = stripe.Event.construct_from(
        values=data,
        key=key
    )
    construct_from_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.stripe'
        '.Event.construct_from',
        return_value=event
    )

    service = WebhookService()
    service.secret = key

    # act
    service.handle(data)

    # assert
    construct_from_mock.assert_called_once_with(
        values=data,
        key=key
    )
    handler_mock.assert_called_once_with(event)


def test_handle__handler_not_exist__log(mocker):

    # arrange
    stripe_id = "prod_O2DByEkAsBnjUC"
    data = {
      "id": "evt_1NG8n1BM2UVM1VfGLv20Skzf",
      "object": "event",
      "api_version": "2022-11-15",
      "created": 1686092147,
      "data": {
        "object": {
          "id": stripe_id,
          "object": "product",
          "active": False,
          "attributes": [
          ],
          "created": 1686092022,
          "default_price": None,
          "description": None,
          "images": [
          ],
          "livemode": False,
          "metadata": {
          },
          "name": "1",
          "package_dimensions": None,
          "shippable": None,
          "statement_descriptor": None,
          "tax_code": None,
          "type": "service",
          "unit_label": None,
          "updated": 1686092147,
          "url": None
        }
      },
      "livemode": False,
      "pending_webhooks": 1,
      "request": {
        "id": "req_oxf7W64DISLKeL",
        "idempotency_key": None
      },
      "type": "payment_method.deatached"
    }
    key = '!@#d'
    event = stripe.Event.construct_from(
        values=data,
        key=key
    )
    construct_from_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.stripe'
        '.Event.construct_from',
        return_value=event
    )
    capture_sentry_message_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.capture_sentry_message'
    )
    service = WebhookService()
    service.secret = key

    # act
    service.handle(data)

    # assert
    construct_from_mock.assert_called_once_with(
        values=data,
        key=key
    )
    capture_sentry_message_mock.assert_called_once_with(
        message='Webhook handler not found',
        level=SentryLogLevel.ERROR,
        data={
            'event_id': event.id,
            'event_type': event.type,
        }
    )


def test_handle__invalid_event__raise_exception(mocker):

    # arrange
    stripe_id = "prod_O2DByEkAsBnjUC"
    data = {
      "id": "evt_1NG8n1BM2UVM1VfGLv20Skzf",
      "object": "event",
      "api_version": "2022-11-15",
      "created": 1686092147,
      "data": {
        "object": {
          "id": stripe_id,
          "object": "product",
          "active": False,
          "attributes": [
          ],
          "created": 1686092022,
          "default_price": None,
          "description": None,
          "images": [
          ],
          "livemode": False,
          "metadata": {
          },
          "name": "1",
          "package_dimensions": None,
          "shippable": None,
          "statement_descriptor": None,
          "tax_code": None,
          "type": "service",
          "unit_label": None,
          "updated": 1686092147,
          "url": None
        }
      },
      "livemode": False,
      "pending_webhooks": 1,
      "request": {
        "id": "req_oxf7W64DISLKeL",
        "idempotency_key": None
      },
      "type": "product.deleted"
    }
    handler_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.WebhookService'
        '._product_deleted'
    )
    message = 'some message'
    construct_from_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.stripe'
        '.Event.construct_from',
        side_effect=WebhookServiceException(message)
    )
    key = '!@#'
    service = WebhookService()
    service.secret = key

    # act
    with pytest.raises(WebhookServiceException) as ex:
        service.handle(data)

    # assert
    assert ex.value.message == message
    construct_from_mock.assert_called_once_with(
        values=data,
        key=key
    )
    handler_mock.assert_not_called()


def test_handle__subscription_not_found__raise(mocker):

    # arrange
    stripe_id = "prod_O2DByEkAsBnjUC"
    data = {
      "id": "evt_1NG8n1BM2UVM1VfGLv20Skzf",
      "object": "event",
      "api_version": "2022-11-15",
      "created": 1686092147,
      "data": {
        "object": {
          "id": stripe_id,
          "object": "product",
          "active": False,
          "attributes": [
          ],
          "created": 1686092022,
          "default_price": None,
          "description": None,
          "images": [
          ],
          "livemode": False,
          "metadata": {
          },
          "name": "1",
          "package_dimensions": None,
          "shippable": None,
          "statement_descriptor": None,
          "tax_code": None,
          "type": "service",
          "unit_label": None,
          "updated": 1686092147,
          "url": None
        }
      },
      "livemode": False,
      "pending_webhooks": 1,
      "request": {
        "id": "req_oxf7W64DISLKeL",
        "idempotency_key": None
      },
      "type": "customer.subscription.updated"
    }
    details = {
        'account_id': 1,
        'subs_metadata': {'account_id': 'incorrect'}
    }
    handler_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.WebhookService'
        '._customer_subscription_updated',
        side_effect=NotFoundAccountForSubscription(
            account_id=1,
            subs_metadata={'account_id': 'incorrect'}
        )
    )
    key = '!@#d'
    event = stripe.Event.construct_from(
        values=data,
        key=key
    )
    construct_from_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.stripe'
        '.Event.construct_from',
        return_value=event
    )

    service = WebhookService()
    service.secret = key

    # act
    with pytest.raises(NotFoundAccountForSubscription) as ex:
        service.handle(data)

    # assert
    assert ex.value.message == messages.MSG_BL_0017
    assert ex.value.details == details
    construct_from_mock.assert_called_once_with(
        values=data,
        key=key
    )
    handler_mock.assert_called_once_with(event)


def test_handle__customer_updated__ok(mocker):

    # arrange
    stripe_id = 'cus_123sd'
    email = 'admin@pneumatic.app'
    phone = '+12015457881'
    account = create_test_account(stripe_id=stripe_id)
    account_owner = create_test_user(
        account=account,
        is_account_owner=True,
        email=email,
        phone='+12015457887'
    )

    data = {
          "id": "evt_1OPiSuBM2UVM1VfGFdeafWPw",
          "object": "event",
          "api_version": "2023-10-16",
          "created": 1703150570,
          "data": {
            "object": {
              "id": stripe_id,
              "object": "customer",
              "address": None,
              "balance": 0,
              "created": 1684925248,
              "currency": "eur",
              "default_source": None,
              "delinquent": False,
              "description": "Admin Dev",
              "discount": None,
              "email": email,
              "invoice_prefix": "F0ECCE48",
              "invoice_settings": {
                "custom_fields": None,
                "default_payment_method": "pm_1OAp4OBM2UVM1VfGx8grVlhS",
                "footer": None,
                "rendering_options": None
              },
              "livemode": False,
              "metadata": {
              },
              "name": "new name",
              "next_invoice_sequence": 81,
              "phone": phone,
              "preferred_locales": [
              ],
              "shipping": None,
              "tax_exempt": "none",
              "test_clock": None
            },
            "previous_attributes": {
              "phone": "+12015457887"
            }
          },
          "livemode": False,
          "pending_webhooks": 1,
          "request": {
            "id": "req_SpaTTpAkluT9qr",
            "idempotency_key": "768cc3a8-7fea-404e-9ef8-d273a2edce4d"
          },
          "type": "customer.updated"
        }
    key = '!@#d'
    event = stripe.Event.construct_from(
        values=data,
        key=key
    )
    get_valid_webhook_account_by_stripe_id_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService._get_valid_webhook_account_by_stripe_id',
        return_value=account
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        '__init__',
        return_value=None
    )
    user_service_update_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.UserService.partial_update'
    )

    service = WebhookService()
    service.secret = key

    # act
    service._customer_updated(event)

    # assert
    get_valid_webhook_account_by_stripe_id_mock.assert_called_once_with(
        stripe_id
    )
    user_service_init_mock.assert_called_once_with(
        auth_type=AuthTokenType.WEBHOOK,
        instance=account_owner
    )
    user_service_update_mock.assert_called_once_with(
        phone=phone,
        force_save=True
    )


def test_handle__customer_updated__account_owner_not_found__raise(mocker):

    # arrange
    stripe_id = 'cus_123sd'
    email = 'admin@pneumatic.app'
    phone = '+12015457881'
    account = create_test_account(stripe_id=stripe_id)
    account_owner = create_test_user(
        account=account,
        is_account_owner=True,
        email='another@test.test',
        phone='+12015457887'
    )

    data = {
        "id": "evt_1OPiSuBM2UVM1VfGFdeafWPw",
        "object": "event",
        "api_version": "2023-10-16",
        "created": 1703150570,
        "data": {
            "object": {
                "id": stripe_id,
                "object": "customer",
                "address": None,
                "balance": 0,
                "created": 1684925248,
                "currency": "eur",
                "default_source": None,
                "delinquent": False,
                "description": "Admin Dev",
                "discount": None,
                "email": email,
                "invoice_prefix": "F0ECCE48",
                "invoice_settings": {
                    "custom_fields": None,
                    "default_payment_method": "pm_1OAp4OBM2UVM1VfGx8grVlhS",
                    "footer": None,
                    "rendering_options": None
                },
                "livemode": False,
                "metadata": {
                },
                "name": "new name",
                "next_invoice_sequence": 81,
                "phone": phone,
                "preferred_locales": [
                ],
                "shipping": None,
                "tax_exempt": "none",
                "test_clock": None
            },
            "previous_attributes": {
                "phone": "+12015457887"
            }
        },
        "livemode": False,
        "pending_webhooks": 1,
        "request": {
            "id": "req_SpaTTpAkluT9qr",
            "idempotency_key": "768cc3a8-7fea-404e-9ef8-d273a2edce4d"
        },
        "type": "customer.updated"
    }
    key = '!@#d'
    event = stripe.Event.construct_from(
        values=data,
        key=key
    )
    get_valid_webhook_account_by_stripe_id_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.'
        'WebhookService._get_valid_webhook_account_by_stripe_id',
        return_value=account
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        '__init__',
        return_value=None
    )
    user_service_update_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.webhooks.UserService.partial_update'
    )

    service = WebhookService()
    service.secret = key

    # act
    with pytest.raises(AccountOwnerNotFound) as ex:
        service._customer_updated(event)

    # assert
    assert ex.value.message == messages.MSG_BL_0020
    assert ex.value.details == {
        'account_id': account.id,
        'customer_email': email,
        'owner_email': account_owner.email,
    }

    get_valid_webhook_account_by_stripe_id_mock.assert_called_once_with(
        stripe_id
    )
    user_service_init_mock.assert_not_called()
    user_service_update_mock.assert_not_called()
