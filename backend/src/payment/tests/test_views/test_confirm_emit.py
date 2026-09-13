import pytest

from src.accounts.enums import BillingPlanType
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
from src.payment.stripe.tokens import ConfirmToken
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_owner,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_confirm__subscription_data__emit_token_user_as_actor(
    mocker,
    api_client,
    fake_stream,
):

    """ The link is signed for the user who started the payment: the
        actor is that user, not whoever follows the link. """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    admin = create_test_admin(account=account)
    subscription_data = {
        'billing_plan': BillingPlanType.PREMIUM,
        'max_users': 5,
        'trial_days': 7,
    }
    token = ConfirmToken()
    token['user_id'] = owner.id
    token['account_id'] = account.id
    token['is_superuser'] = False
    token['auth_type'] = AuthTokenType.API
    token['subscription'] = subscription_data
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    confirm_mock = mocker.patch.object(
        StripeService,
        attribute='confirm',
    )
    api_client.token_authenticate(user=admin)

    # act
    response = api_client.get(
        path='/payment/confirm',
        data={'token': str(token)},
    )

    # assert
    assert response.status_code == 204
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.BILLING_PAYMENT_CONFIRM
    assert event.category == EventCategory.AUDIT
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.API_KEY,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.ACCOUNT,
        id=account.id,
    )
    assert event.payload == {
        'billing_plan': BillingPlanType.PREMIUM,
        'max_users': 5,
    }
    stripe_service_init_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.API,
        is_superuser=False,
    )
    confirm_mock.assert_called_once_with(
        subscription_data=subscription_data,
    )


def test_confirm__no_subscription_data__emit_empty_payload(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    token = ConfirmToken()
    token['user_id'] = owner.id
    token['account_id'] = account.id
    token['is_superuser'] = False
    token['auth_type'] = AuthTokenType.USER
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    confirm_mock = mocker.patch.object(
        StripeService,
        attribute='confirm',
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.get(
        path='/payment/confirm',
        data={'token': str(token)},
    )

    # assert
    assert response.status_code == 204
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.BILLING_PAYMENT_CONFIRM
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
    assert event.payload == {}
    stripe_service_init_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    confirm_mock.assert_called_once_with(subscription_data=None)


def test_confirm__service_exception__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    token = ConfirmToken()
    token['user_id'] = owner.id
    token['account_id'] = account.id
    token['is_superuser'] = False
    token['auth_type'] = AuthTokenType.USER
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    confirm_mock = mocker.patch.object(
        StripeService,
        attribute='confirm',
        side_effect=StripeServiceException(message=messages.MSG_BL_0009),
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.get(
        path='/payment/confirm',
        data={'token': str(token)},
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
    confirm_mock.assert_called_once_with(subscription_data=None)


def test_confirm__billing_sync_off__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account(billing_sync=False)
    owner = create_test_owner(account=account)
    token = ConfirmToken()
    token['user_id'] = owner.id
    token['account_id'] = account.id
    token['is_superuser'] = False
    token['auth_type'] = AuthTokenType.USER
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    confirm_mock = mocker.patch.object(
        StripeService,
        attribute='confirm',
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.get(
        path='/payment/confirm',
        data={'token': str(token)},
    )

    # assert
    assert response.status_code == 204
    assert fake_stream.events == []
    stripe_service_init_mock.assert_not_called()
    confirm_mock.assert_not_called()


def test_confirm__expired_token__no_event(
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
    confirm_mock = mocker.patch.object(
        StripeService,
        attribute='confirm',
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.get(
        path='/payment/confirm',
        data={'token': 'invalid-token'},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_BL_0001
    assert response.data['details']['name'] == 'token'
    assert response.data['details']['reason'] == messages.MSG_BL_0001
    assert fake_stream.events == []
    stripe_service_init_mock.assert_not_called()
    confirm_mock.assert_not_called()
