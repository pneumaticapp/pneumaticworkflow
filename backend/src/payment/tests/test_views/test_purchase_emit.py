import pytest

from src.authentication.enums import AuthTokenType
from src.logs.events.enums import (
    ActorType,
    EventCategory,
    EventName,
    EventObjectType,
)
from src.logs.events.schema import Actor, EventObject
from src.payment import messages
from src.payment.stripe.exceptions import StripeServiceException
from src.payment.stripe.service import StripeService
from src.payment.tests.fixtures import (
    create_test_invoice_price,
    create_test_product,
    create_test_recurring_price,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_purchase__payment_link__emit_checkout_required(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    recurring_price = create_test_recurring_price(
        product=create_test_product(code='premium', stripe_id='prod_1'),
    )
    invoice_price = create_test_invoice_price(
        product=create_test_product(
            code='addon',
            stripe_id='prod_2',
            is_subscription=False,
        ),
    )
    success_url = 'http://localhost/success/'
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    create_purchase_mock = mocker.patch.object(
        StripeService,
        attribute='create_purchase',
        return_value='checkout.stripe.com',
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.post(
        path='/payment/purchase',
        data={
            'success_url': success_url,
            'products': [
                {'code': recurring_price.code, 'quantity': 3},
                {'code': invoice_price.code, 'quantity': 1},
            ],
        },
        format='json',
    )

    # assert
    assert response.status_code == 200
    assert response.data['payment_link'] == 'checkout.stripe.com'
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.BILLING_PURCHASE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.ACCOUNT,
        id=account.id,
    )
    assert event.payload == {
        'products': {
            recurring_price.code: 3,
            invoice_price.code: 1,
        },
        'checkout_required': True,
    }
    stripe_service_init_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    create_purchase_mock.assert_called_once_with(
        success_url=success_url,
        products=[
            {'code': recurring_price.code, 'quantity': 3},
            {'code': invoice_price.code, 'quantity': 1},
        ],
    )


def test_purchase__off_session__emit_checkout_not_required(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    price = create_test_recurring_price()
    success_url = 'http://localhost/success/'
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    create_purchase_mock = mocker.patch.object(
        StripeService,
        attribute='create_purchase',
        return_value=None,
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.post(
        path='/payment/purchase',
        data={
            'success_url': success_url,
            'products': [{'code': price.code, 'quantity': 2}],
        },
        format='json',
    )

    # assert
    assert response.status_code == 204
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.BILLING_PURCHASE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.ACCOUNT,
        id=account.id,
    )
    assert event.payload == {
        'products': {price.code: 2},
        'checkout_required': False,
    }
    stripe_service_init_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    create_purchase_mock.assert_called_once_with(
        success_url=success_url,
        products=[{'code': price.code, 'quantity': 2}],
    )


def test_purchase__repeated_code__emit_summed_quantity(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    price = create_test_recurring_price()
    success_url = 'http://localhost/success/'
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    create_purchase_mock = mocker.patch.object(
        StripeService,
        attribute='create_purchase',
        return_value=None,
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.post(
        path='/payment/purchase',
        data={
            'success_url': success_url,
            'products': [
                {'code': price.code, 'quantity': 1},
                {'code': price.code, 'quantity': 5},
            ],
        },
        format='json',
    )

    # assert
    assert response.status_code == 204
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.BILLING_PURCHASE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.ACCOUNT,
        id=account.id,
    )
    assert event.payload == {
        'products': {price.code: 6},
        'checkout_required': False,
    }
    stripe_service_init_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    create_purchase_mock.assert_called_once_with(
        success_url=success_url,
        products=[
            {'code': price.code, 'quantity': 1},
            {'code': price.code, 'quantity': 5},
        ],
    )


def test_purchase__service_exception__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    owner = create_test_owner()
    price = create_test_recurring_price()
    success_url = 'http://localhost/success/'
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    create_purchase_mock = mocker.patch.object(
        StripeService,
        attribute='create_purchase',
        side_effect=StripeServiceException(message=messages.MSG_BL_0009),
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.post(
        path='/payment/purchase',
        data={
            'success_url': success_url,
            'products': [{'code': price.code, 'quantity': 1}],
        },
        format='json',
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_BL_0009
    assert response.data['details'] == {}
    assert fake_stream.events == []
    stripe_service_init_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    create_purchase_mock.assert_called_once_with(
        success_url=success_url,
        products=[{'code': price.code, 'quantity': 1}],
    )


def test_purchase__billing_sync_off__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account(billing_sync=False)
    owner = create_test_owner(account=account)
    price = create_test_recurring_price()
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    create_purchase_mock = mocker.patch.object(
        StripeService,
        attribute='create_purchase',
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.post(
        path='/payment/purchase',
        data={
            'success_url': 'http://localhost/success/',
            'products': [{'code': price.code, 'quantity': 1}],
        },
        format='json',
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_BL_0018
    assert response.data['details'] == {}
    assert fake_stream.events == []
    stripe_service_init_mock.assert_not_called()
    create_purchase_mock.assert_not_called()


def test_purchase__empty_products__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    owner = create_test_owner()
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    create_purchase_mock = mocker.patch.object(
        StripeService,
        attribute='create_purchase',
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.post(
        path='/payment/purchase',
        data={
            'success_url': 'http://localhost/success/',
            'products': [],
        },
        format='json',
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_BL_0002
    assert response.data['details']['name'] == 'products'
    assert response.data['details']['reason'] == messages.MSG_BL_0002
    assert fake_stream.events == []
    stripe_service_init_mock.assert_not_called()
    create_purchase_mock.assert_not_called()
