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
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_owner,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_cancel__owner__emit_subscription_cancel(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    cancel_subscription_mock = mocker.patch.object(
        StripeService,
        attribute='cancel_subscription',
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.post(path='/payment/subscription/cancel')

    # assert
    assert response.status_code == 204
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.BILLING_SUBSCRIPTION_CANCEL
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
    cancel_subscription_mock.assert_called_once_with()


def test_cancel__admin__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    admin = create_test_admin()
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    cancel_subscription_mock = mocker.patch.object(
        StripeService,
        attribute='cancel_subscription',
    )
    api_client.token_authenticate(user=admin)

    # act
    response = api_client.post(path='/payment/subscription/cancel')

    # assert
    assert response.status_code == 403
    assert fake_stream.events == []
    stripe_service_init_mock.assert_not_called()
    cancel_subscription_mock.assert_not_called()


def test_cancel__service_exception__no_event(
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
    cancel_subscription_mock = mocker.patch.object(
        StripeService,
        attribute='cancel_subscription',
        side_effect=StripeServiceException(message=messages.MSG_BL_0005),
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.post(path='/payment/subscription/cancel')

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_BL_0005
    assert response.data['details'] == {}
    assert fake_stream.events == []
    stripe_service_init_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    cancel_subscription_mock.assert_called_once_with()


def test_cancel__billing_sync_off__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account(billing_sync=False)
    owner = create_test_owner(account=account)
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    cancel_subscription_mock = mocker.patch.object(
        StripeService,
        attribute='cancel_subscription',
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.post(path='/payment/subscription/cancel')

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_BL_0018
    assert response.data['details'] == {}
    assert fake_stream.events == []
    stripe_service_init_mock.assert_not_called()
    cancel_subscription_mock.assert_not_called()
