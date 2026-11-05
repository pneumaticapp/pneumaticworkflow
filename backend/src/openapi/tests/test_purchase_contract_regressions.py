"""Purchase contracts retain live validation and execute the Stripe service."""

import inspect
import json
from typing import Any
from urllib.parse import parse_qs, urlsplit

from django.core.cache import caches
from django.test import RequestFactory
from jsonschema.exceptions import ValidationError
import pytest
from rest_framework import serializers
from rest_framework.fields import SkipField
import stripe

from src.accounts.enums import BillingPlanType
from src.accounts.models import User
from src.generics.tests.clients import PneumaticApiClient
from src.openapi.tests.http_contracts import HttpContract
from src.payment.models import Price
from src.payment.serializers import PurchaseSerializer
from src.payment.stripe.service import StripeService
from src.payment.stripe.tokens import ConfirmToken
from src.payment.tests.fixtures import (
    create_test_invoice_price,
    create_test_product,
)
from src.processes.tests.fixtures import create_test_account, create_test_owner


PATH = '/payment/purchase'
SUCCESS_URL = 'https://example.test/billing/success'
CANCEL_URL = 'https://example.test/billing/cancel'
CHECKOUT_URL = 'https://checkout.stripe.com/c/pay/cs_purchase_contract'
CUSTOMER_ID = 'cus_purchase_contract'
PAYMENT_METHOD_ID = 'pm_purchase_contract'
PRICE_CODE = 'purchase_contract_addon'
PRICE_ID = 'price_purchase_contract'
QUANTITY = 2
MOCKED_PURCHASE_CASES = (
    'src/payment/tests/test_views/test_purchase.py'
    '::test_purchase__payment_link__ok',
    'src/payment/tests/test_views/test_purchase.py'
    '::test_purchase__off_session__ok',
)


def purchase_payload() -> dict:
    return {
        'success_url': SUCCESS_URL,
        'cancel_url': CANCEL_URL,
        'products': [{'code': PRICE_CODE, 'quantity': QUANTITY}],
    }


@pytest.fixture
def purchase_owner(
    contract_api_client: PneumaticApiClient, settings: Any, db: None,
) -> User:
    settings.PRIVATE_API_CHECK_IP = False
    for alias in ('default', 'auth', 'session'):
        caches[alias].clear()
    account = create_test_account(stripe_id=CUSTOMER_ID, billing_sync=True)
    owner = create_test_owner(account=account)
    contract_api_client.token_authenticate(owner)
    return owner


@pytest.fixture
def purchase_price(purchase_owner: User) -> Price:
    product = create_test_product(
        stripe_id='prod_purchase_contract',
        code='purchase_contract_addon',
        is_subscription=False,
    )
    return create_test_invoice_price(
        product=product, code=PRICE_CODE, stripe_id=PRICE_ID,
        min_quantity=1, max_quantity=5,
    )


@pytest.fixture
def purchase_sdk(mocker: Any) -> dict:
    customer = stripe.Customer.construct_from({
        'id': CUSTOMER_ID,
        'object': 'customer',
        'invoice_settings': {'default_payment_method': None},
    }, None)
    payment_method = stripe.PaymentMethod.construct_from({
        'id': PAYMENT_METHOD_ID,
        'object': 'payment_method',
        'type': 'card',
        'card': {'brand': 'visa', 'last4': '4242'},
    }, None)
    checkout = stripe.checkout.Session.construct_from({
        'id': 'cs_purchase_contract',
        'object': 'checkout.session',
        'url': CHECKOUT_URL,
    }, None)
    invoice = stripe.Invoice.construct_from({
        'id': 'in_purchase_contract', 'object': 'invoice', 'status': 'draft',
    }, None)
    invoice_item = stripe.InvoiceItem.construct_from({
        'id': 'ii_purchase_contract', 'object': 'invoiceitem',
    }, None)

    def empty_list(url: str) -> stripe.ListObject:
        return stripe.ListObject.construct_from({
            'object': 'list', 'url': url, 'has_more': False, 'data': [],
        }, None)

    # These are external SDK boundaries, not application service methods.
    calls = {
        'customer': mocker.patch(
            'stripe.Customer.retrieve', return_value=customer,
        ),
        'subscriptions': mocker.patch(
            'stripe.Subscription.list',
            return_value=empty_list('/v1/subscriptions'),
        ),
        'payment_method': mocker.patch(
            'stripe.PaymentMethod.retrieve', return_value=payment_method,
        ),
        'payment_methods': mocker.patch(
            'stripe.PaymentMethod.list',
            return_value=empty_list('/v1/payment_methods'),
        ),
        'checkout_sessions': mocker.patch(
            'stripe.checkout.Session.list',
            return_value=empty_list('/v1/checkout/sessions'),
        ),
        'checkout': mocker.patch(
            'stripe.checkout.Session.create', return_value=checkout,
        ),
        'invoice': mocker.patch('stripe.Invoice.create', return_value=invoice),
        'invoice_item': mocker.patch(
            'stripe.InvoiceItem.create', return_value=invoice_item,
        ),
        'finalize_invoice': mocker.patch(
            'stripe.Invoice.finalize_invoice', return_value=invoice,
        ),
        'pay_invoice': mocker.patch(
            'stripe.Invoice.pay', return_value=invoice,
        ),
    }
    return {'customer': customer, 'invoice': invoice, 'calls': calls}


@pytest.mark.parametrize('status', [200, 204])
def test_purchase__real_stripe_service__both_success_contracts(
    contract_api_client: PneumaticApiClient,
    purchase_owner: User,
    purchase_price: Price,
    purchase_sdk: dict,
    status: int,
) -> None:
    customer = purchase_sdk['customer']
    if status == 204:
        customer['invoice_settings']['default_payment_method'] = (
            PAYMENT_METHOD_ID
        )

    response = contract_api_client.post(
        PATH, data=purchase_payload(), format='json',
    )

    assert response.status_code == status
    calls = purchase_sdk['calls']
    calls['customer'].assert_called_once_with(id=CUSTOMER_ID)
    calls['subscriptions'].assert_called_once_with(customer=customer)
    if status == 200:
        assert response.json() == {'payment_link': CHECKOUT_URL}
        calls['payment_methods'].assert_called_once_with(customer=customer)
        calls['payment_method'].assert_not_called()
        calls['checkout_sessions'].assert_called_once_with(
            customer=customer, status='open',
        )
        calls['checkout'].assert_called_once()
        arguments = calls['checkout'].call_args.kwargs
        assert arguments['customer'] is customer
        assert arguments['cancel_url'] == CANCEL_URL
        assert arguments['mode'] == 'payment'
        assert arguments['allow_promotion_codes'] is True
        assert arguments['line_items'] == [{
            'price': PRICE_ID,
            'quantity': QUANTITY,
            'adjustable_quantity': {
                'enabled': True, 'maximum': 5, 'minimum': 1,
            },
        }]
        return_url = urlsplit(arguments['success_url'])
        assert return_url._replace(query='').geturl() == SUCCESS_URL
        token_query = parse_qs(return_url.query)
        assert set(token_query) == {'token'}
        token = ConfirmToken(token_query['token'][0])
        assert token['user_id'] == purchase_owner.id
        assert token['account_id'] == purchase_owner.account_id
        assert token['is_superuser'] is False
        for name in ('invoice', 'invoice_item', 'finalize_invoice',
                     'pay_invoice'):
            calls[name].assert_not_called()
    else:
        assert not response.content
        calls['payment_method'].assert_called_once_with(id=PAYMENT_METHOD_ID)
        calls['payment_methods'].assert_not_called()
        calls['checkout_sessions'].assert_not_called()
        calls['checkout'].assert_not_called()
        calls['invoice'].assert_called_once_with(
            customer=customer, collection_method='charge_automatically',
        )
        calls['invoice_item'].assert_called_once_with(
            invoice=purchase_sdk['invoice'], customer=customer,
            price=PRICE_ID, quantity=QUANTITY,
        )
        calls['finalize_invoice'].assert_called_once_with()
        calls['pay_invoice'].assert_called_once_with()
    purchase_price.refresh_from_db()
    assert purchase_price.is_deleted is False
    purchase_owner.account.refresh_from_db()
    assert purchase_owner.account.billing_plan == BillingPlanType.FREEMIUM


@pytest.mark.parametrize('invalid', [
    'missing-success', 'invalid-success', 'missing-products',
    'empty-products', 'unknown-price',
])
def test_purchase__invalid_input__rejected_before_stripe(
    contract_api_client: PneumaticApiClient,
    purchase_price: Price,
    purchase_sdk: dict,
    invalid: str,
) -> None:
    payload = purchase_payload()
    if invalid == 'missing-success':
        payload.pop('success_url')
    elif invalid == 'invalid-success':
        payload['success_url'] = 'not-a-url'
    elif invalid == 'missing-products':
        payload.pop('products')
    elif invalid == 'empty-products':
        payload['products'] = []
    else:
        payload['products'] = [{
            'code': 'unknown-purchase-price', 'quantity': 1,
        }]

    response = contract_api_client.post(PATH, data=payload, format='json')

    assert response.status_code == 400
    assert response.json()['code'] == 'validation_error'
    name = 'success_url' if invalid.endswith('success') else 'products'
    assert response.json()['details']['name'] == name
    for boundary in purchase_sdk['calls'].values():
        boundary.assert_not_called()


def test_purchase__billing_sync_disabled__rejected_before_stripe(
    contract_api_client: PneumaticApiClient,
    purchase_owner: User,
    purchase_price: Price,
    purchase_sdk: dict,
) -> None:
    account = purchase_owner.account
    account.billing_sync = False
    account.save(update_fields=['billing_sync'])

    response = contract_api_client.post(
        PATH, data=purchase_payload(), format='json',
    )

    assert response.status_code == 400
    assert response.json()['code'] == 'validation_error'
    for boundary in purchase_sdk['calls'].values():
        boundary.assert_not_called()


@pytest.mark.parametrize('name', ['success_url', 'cancel_url', 'products'])
def test_purchase__schema__all_service_arguments_are_required(
    http_contract: HttpContract, name: str,
) -> None:
    operation = http_contract.document['paths'][PATH]['post']
    media = operation['requestBody']['content']['application/json']
    schema = http_contract.resolve(media['schema'])

    assert name in schema['required']
    field = schema['properties'][name]
    if name == 'products':
        assert field['type'] == 'array'
    else:
        assert field['type'] == 'string'
        assert field['format'] == 'uri'
        assert field['minLength'] == 1
        assert field.get('nullable', False) == (name == 'cancel_url')


def test_purchase__schema__omitted_cancel_url_is_rejected(
    http_contract: HttpContract,
) -> None:
    operation = http_contract.document['paths'][PATH]['post']
    payload = purchase_payload()
    payload.pop('cancel_url')
    body = json.dumps(payload).encode('utf-8')
    request = RequestFactory().post(
        PATH, data=body, content_type='application/json',
    )

    with pytest.raises(ValidationError, match='cancel_url'):
        http_contract.request_body(operation, request, body)


@pytest.mark.parametrize('value', [serializers.empty, None], ids=[
    'omitted', 'null',
])
def test_purchase__live_field__optional_nullable_behavior_is_unchanged(
    value: Any,
) -> None:
    field = PurchaseSerializer().fields['cancel_url']

    assert type(field) is serializers.URLField
    assert field.required is False
    assert field.allow_null is True
    assert field.allow_blank is False
    assert field.default is serializers.empty
    assert PurchaseSerializer._declared_fields['cancel_url'].required is False
    if value is serializers.empty:
        with pytest.raises(SkipField):
            field.run_validation(value)
    else:
        assert field.run_validation(value) is None


def test_purchase__service_signature__still_requires_cancel_url() -> None:
    signature = inspect.signature(StripeService.create_purchase)
    payload = purchase_payload()
    payload.pop('cancel_url')

    cancel_url = signature.parameters['cancel_url']
    assert cancel_url.default is inspect.Parameter.empty
    with pytest.raises(TypeError, match='cancel_url'):
        signature.bind(None, **payload)


@pytest.mark.parametrize('case', MOCKED_PURCHASE_CASES)
def test_purchase__mocked_service_case__excluded_from_contract_registry(
    pytestconfig: Any, case: str,
) -> None:
    assert case not in pytestconfig._api_contract_cases
