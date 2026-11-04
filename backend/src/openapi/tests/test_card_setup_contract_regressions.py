"""Card setup contracts exercise the real service and Stripe SDK boundary."""

import inspect
from typing import Any
from urllib.parse import parse_qs, urlsplit

from django.core.cache import caches
from django.http import QueryDict
from django.test import RequestFactory
import pytest
from rest_framework import serializers
import stripe

from src.accounts.models import User
from src.generics.tests.clients import PneumaticApiClient
from src.openapi.tests.http_contracts import HttpContract
from src.payment.serializers import CardSetupSerializer
from src.payment.stripe.service import StripeService
from src.payment.stripe.tokens import ConfirmToken
from src.processes.tests.fixtures import create_test_account, create_test_owner


PATH = '/payment/card-setup'
SUCCESS_URL = 'https://example.test/billing/success'
CANCEL_URL = 'https://example.test/billing/cancel'
SETUP_LINK = 'https://checkout.stripe.com/c/pay/cs_contract'
CUSTOMER_ID = 'cus_card_contract'
PAYMENT_METHOD_ID = 'pm_card_contract'
MOCKED_CARD_CASES = (
    'src/payment/tests/test_views/test_card_setup.py'
    '::test_card_setup__payment_link__ok',
    'src/payment/tests/test_views/test_card_setup.py'
    '::test_card_setup__service_exception__validation_error',
)


@pytest.fixture
def card_setup_owner(
    contract_api_client: PneumaticApiClient, settings: Any, db: None,
) -> User:
    settings.PRIVATE_API_CHECK_IP = False
    for alias in ('default', 'auth', 'session'):
        caches[alias].clear()
    account = create_test_account(
        stripe_id=CUSTOMER_ID, billing_sync=False,
    )
    owner = create_test_owner(account=account)
    contract_api_client.token_authenticate(owner)
    return owner


@pytest.fixture
def stripe_sdk(mocker: Any) -> dict:
    customer = stripe.Customer.construct_from({
        'id': CUSTOMER_ID,
        'object': 'customer',
        'invoice_settings': {'default_payment_method': PAYMENT_METHOD_ID},
    }, None)
    payment_method = stripe.PaymentMethod.construct_from({
        'id': PAYMENT_METHOD_ID,
        'object': 'payment_method',
        'type': 'card',
        'card': {'brand': 'visa', 'last4': '4242'},
    }, None)
    checkout = stripe.checkout.Session.construct_from({
        'id': 'cs_contract', 'object': 'checkout.session', 'url': SETUP_LINK,
    }, None)
    subscriptions = stripe.ListObject.construct_from({
        'object': 'list', 'url': '/v1/subscriptions',
        'has_more': False, 'data': [],
    }, None)
    sessions = stripe.ListObject.construct_from({
        'object': 'list', 'url': '/v1/checkout/sessions',
        'has_more': False, 'data': [],
    }, None)
    # Only SDK calls cross the external boundary; services stay executable.
    return {
        'customer': customer,
        'retrieve_customer': mocker.patch(
            'stripe.Customer.retrieve', return_value=customer,
        ),
        'list_subscriptions': mocker.patch(
            'stripe.Subscription.list', return_value=subscriptions,
        ),
        'retrieve_payment_method': mocker.patch(
            'stripe.PaymentMethod.retrieve', return_value=payment_method,
        ),
        'list_sessions': mocker.patch(
            'stripe.checkout.Session.list', return_value=sessions,
        ),
        'create_session': mocker.patch(
            'stripe.checkout.Session.create', return_value=checkout,
        ),
    }


def test_card_setup__real_stripe_service__matches_contract(
    contract_api_client: PneumaticApiClient,
    card_setup_owner: User,
    stripe_sdk: dict,
) -> None:
    response = contract_api_client.get(PATH, data={
        'success_url': SUCCESS_URL, 'cancel_url': CANCEL_URL,
    })

    assert response.status_code == 200
    assert response.json() == {'setup_link': SETUP_LINK}
    customer = stripe_sdk['customer']
    stripe_sdk['retrieve_customer'].assert_called_once_with(id=CUSTOMER_ID)
    stripe_sdk['list_subscriptions'].assert_called_once_with(
        customer=customer,
    )
    stripe_sdk['retrieve_payment_method'].assert_called_once_with(
        id=PAYMENT_METHOD_ID,
    )
    stripe_sdk['list_sessions'].assert_called_once_with(
        customer=customer, status='open',
    )
    stripe_sdk['create_session'].assert_called_once()
    arguments = stripe_sdk['create_session'].call_args.kwargs
    assert set(arguments) == {
        'customer', 'client_reference_id', 'success_url', 'cancel_url',
        'mode', 'payment_method_types',
    }
    assert arguments['customer'] is customer
    assert arguments['cancel_url'] == CANCEL_URL
    assert arguments['mode'] == 'setup'
    assert arguments['payment_method_types'] == ['card']
    assert len(arguments['client_reference_id']) == 40
    return_url = urlsplit(arguments['success_url'])
    assert return_url._replace(query='').geturl() == SUCCESS_URL
    token_query = parse_qs(return_url.query)
    assert set(token_query) == {'token'}
    token = ConfirmToken(token_query['token'][0])
    assert token['user_id'] == card_setup_owner.id
    assert token['account_id'] == card_setup_owner.account_id
    assert token['is_superuser'] is False


@pytest.mark.parametrize('success_url', [None, 'not-a-url'])
def test_card_setup__invalid_success_url__rejected_before_stripe(
    contract_api_client: PneumaticApiClient,
    card_setup_owner: User,
    stripe_sdk: dict,
    success_url: Any,
) -> None:
    query = {'cancel_url': CANCEL_URL}
    if success_url is not None:
        query['success_url'] = success_url

    response = contract_api_client.get(PATH, data=query)

    assert response.status_code == 400
    assert response.json()['code'] == 'validation_error'
    assert response.json()['details']['name'] == 'success_url'
    for name, boundary in stripe_sdk.items():
        if name != 'customer':
            boundary.assert_not_called()


@pytest.mark.parametrize('name', ['success_url', 'cancel_url'])
def test_card_setup__schema__both_query_urls_are_required(
    http_contract: HttpContract, name: str,
) -> None:
    parameters = http_contract.document['paths'][PATH]['get']['parameters']
    parameter = next(item for item in parameters if item['name'] == name)

    assert parameter['in'] == 'query'
    assert parameter.get('required') is True
    assert parameter['schema']['type'] == 'string'
    assert parameter['schema']['format'] == 'uri'
    assert parameter['schema']['minLength'] == 1
    assert parameter['schema'].get('nullable', False) == (name == 'cancel_url')


@pytest.mark.parametrize('cancel_url', [serializers.empty, None], ids=[
    'omitted', 'null',
])
def test_card_setup__live_serializer__optional_nullable_field_is_unchanged(
    cancel_url: Any,
) -> None:
    query = {'success_url': SUCCESS_URL}
    if cancel_url is serializers.empty:
        data = QueryDict('', mutable=True)
        data.update(query)
    else:
        data = {**query, 'cancel_url': cancel_url}
    serializer = CardSetupSerializer(data=data)

    assert serializer.is_valid(), serializer.errors
    field = serializer.fields['cancel_url']
    assert type(field) is serializers.URLField
    assert field.required is False
    assert field.allow_null is True
    assert field.allow_blank is False
    assert field.default is serializers.empty
    if cancel_url is serializers.empty:
        assert 'cancel_url' not in serializer.validated_data
    else:
        assert serializer.validated_data['cancel_url'] is None


def test_card_setup__schema__omitted_cancel_url_is_rejected(
    http_contract: HttpContract,
) -> None:
    operation = http_contract.document['paths'][PATH]['get']
    request = RequestFactory().get(PATH, data={'success_url': SUCCESS_URL})

    with pytest.raises(AssertionError, match='Missing cancel_url'):
        http_contract.request_parameters(operation['parameters'], {}, request)


def test_card_setup__service_signature__still_requires_cancel_url() -> None:
    signature = inspect.signature(
        StripeService.get_payment_method_checkout_link,
    )

    cancel_url = signature.parameters['cancel_url']
    assert cancel_url.default is inspect.Parameter.empty
    with pytest.raises(TypeError, match='cancel_url'):
        signature.bind(None, success_url=SUCCESS_URL)


@pytest.mark.parametrize('case', MOCKED_CARD_CASES)
def test_card_setup__mocked_service_case__excluded_from_contract_registry(
    pytestconfig: Any, case: str,
) -> None:
    assert case not in pytestconfig._api_contract_cases
