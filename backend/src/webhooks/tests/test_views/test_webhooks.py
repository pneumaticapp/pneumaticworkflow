import pytest

from src.authentication.enums import AuthTokenType
from src.logs.events.schema import Actor, EventObject
from src.logs.events.enums import (
    ActorType,
    EventName,
    EventObjectType,
)
from src.processes.tests.fixtures import (
    create_test_not_admin,
    create_test_owner,
)
from src.utils.validation import ErrorCode
from src.webhooks.services import ALL_EVENTS

pytestmark = pytest.mark.django_db


def test_subscribe__ok(api_client, mocker):

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)
    url = 'https://192.0.2.1/hook'
    service_mock = mocker.patch(
        'src.webhooks.views.webhooks.WebhookService.subscribe',
    )

    # act
    response = api_client.post(
        path='/webhooks/subscribe',
        data={'url': url},
    )

    # assert
    assert response.status_code == 204
    service_mock.assert_called_once_with(url=url)


def test_subscribe__invalid_url__validation_error(api_client, mocker):

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)
    url = 'undefined'
    service_mock = mocker.patch(
        'src.webhooks.views.webhooks.WebhookService.subscribe',
    )

    # act
    response = api_client.post(
        path='/webhooks/subscribe',
        data={'url': url},
    )

    # assert
    assert response.status_code == 400
    message = 'Enter a valid URL.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'url'
    service_mock.assert_not_called()


def test_subscribe__not_admin__permission_denied(api_client, mocker):

    # arrange
    user = create_test_not_admin()
    api_client.token_authenticate(user)
    url = 'https://192.0.2.1/hook'
    service_mock = mocker.patch(
        'src.webhooks.views.webhooks.WebhookService.subscribe',
    )

    # act
    response = api_client.post(
        path='/webhooks/subscribe',
        data={'url': url},
    )

    # assert
    assert response.status_code == 403
    service_mock.assert_not_called()


def test_unsubscribe__ok(api_client, mocker):

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)
    service_mock = mocker.patch(
        'src.webhooks.views.webhooks.WebhookService.unsubscribe',
    )

    # act
    response = api_client.post(path='/webhooks/unsubscribe')

    # assert
    assert response.status_code == 204
    service_mock.assert_called_once_with()


def test_subscribe__api_key__emit_api_key_actor(
    api_client,
    mocker,
    fake_stream,
):

    """ The service has no request: the kind of the caller comes
        from the token type the view hands over, and the address and
        the browser from the middleware context. """

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user, token_type=AuthTokenType.API)
    webhooks_subscribed_mock = mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.webhooks_subscribed',
    )
    analysis_mock = mocker.patch(
        'src.analysis.services.AnalyticService.'
        'accounts_webhooks_subscribed',
    )

    # act
    response = api_client.post(
        path='/webhooks/subscribe',
        data={'url': 'https://192.0.2.1/hook'},
        HTTP_X_REQUEST_ID='audit-webhook-1',
    )

    # assert
    assert response.status_code == 204
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.WEBHOOK_SUBSCRIBE
    assert event.account_id == user.account_id
    assert event.actor == Actor(
        type=ActorType.API_KEY,
        id=user.id,
        email=user.email,
    )
    assert event.object == EventObject(type=EventObjectType.WEBHOOK)
    assert event.payload == {
        'url': 'https://192.0.2.1/hook',
        'event': ALL_EVENTS,
    }
    assert event.ip == '192.168.0.1'
    assert event.user_agent == 'Firefox'
    assert event.request_id == 'audit-webhook-1'
    webhooks_subscribed_mock.assert_called_once_with()
    analysis_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
    )
