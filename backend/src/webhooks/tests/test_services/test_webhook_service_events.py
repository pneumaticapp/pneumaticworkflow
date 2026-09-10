import pytest

from src.authentication.enums import AuthTokenType
from src.logs.events import Actor, EventObject
from src.logs.events.enums import (
    ActorType,
    EventName,
    EventObjectType,
)
from src.processes.tests.fixtures import create_test_owner
from src.webhooks.enums import HookEvent
from src.webhooks.services import ALL_EVENTS, WebhookService
from src.webhooks.tests.fixtures import (
    create_test_webhook,
    create_test_webhooks,
)

pytestmark = pytest.mark.django_db


def test_subscribe__all_events__emit_webhook_subscribe(mocker):

    # arrange
    user = create_test_owner()
    url = 'https://93.184.216.34/hook'
    emit_mock = mocker.patch('src.logs.events.mixins.emit')
    webhooks_subscribed_mock = mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.webhooks_subscribed',
    )
    analysis_mock = mocker.patch(
        'src.analysis.services.AnalyticService.'
        'accounts_webhooks_subscribed',
    )
    service = WebhookService(user=user)

    # act
    service.subscribe(url=url)

    # assert
    emit_mock.assert_called_once_with(
        EventName.WEBHOOK_SUBSCRIBE,
        account_id=user.account_id,
        actor=Actor(
            type=ActorType.USER,
            id=user.id,
            email=user.email,
        ),
        event_object=EventObject(type=EventObjectType.WEBHOOK),
        payload={'url': url, 'event': ALL_EVENTS},
    )
    webhooks_subscribed_mock.assert_called_once_with()
    analysis_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
    )


def test_subscribe__api_key_auth__emit_api_key_actor_type(mocker):

    # arrange
    user = create_test_owner()
    url = 'https://93.184.216.34/hook'
    emit_mock = mocker.patch('src.logs.events.mixins.emit')
    webhooks_subscribed_mock = mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.webhooks_subscribed',
    )
    analysis_mock = mocker.patch(
        'src.analysis.services.AnalyticService.'
        'accounts_webhooks_subscribed',
    )
    service = WebhookService(user=user, auth_type=AuthTokenType.API)

    # act
    service.subscribe(url=url)

    # assert
    emit_mock.assert_called_once_with(
        EventName.WEBHOOK_SUBSCRIBE,
        account_id=user.account_id,
        actor=Actor(
            type=ActorType.API_KEY,
            id=user.id,
            email=user.email,
        ),
        event_object=EventObject(type=EventObjectType.WEBHOOK),
        payload={'url': url, 'event': ALL_EVENTS},
    )
    webhooks_subscribed_mock.assert_called_once_with()
    analysis_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
    )


def test_subscribe_event__single_event__emit_webhook_subscribe(mocker):

    # arrange
    user = create_test_owner()
    event = HookEvent.WORKFLOW_STARTED
    url = 'https://93.184.216.34/hook'
    emit_mock = mocker.patch('src.logs.events.mixins.emit')
    webhooks_subscribed_mock = mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.webhooks_subscribed',
    )
    analysis_mock = mocker.patch(
        'src.analysis.services.AnalyticService.'
        'accounts_webhooks_subscribed',
    )
    service = WebhookService(user=user)

    # act
    service.subscribe_event(url=url, event=event)

    # assert
    emit_mock.assert_called_once_with(
        EventName.WEBHOOK_SUBSCRIBE,
        account_id=user.account_id,
        actor=Actor(
            type=ActorType.USER,
            id=user.id,
            email=user.email,
        ),
        event_object=EventObject(type=EventObjectType.WEBHOOK),
        payload={'url': url, 'event': event},
    )
    webhooks_subscribed_mock.assert_called_once_with()
    analysis_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
    )


def test_unsubscribe__all_events__emit_webhook_unsubscribe(mocker):

    # arrange
    user = create_test_owner()
    url = 'https://93.184.216.34/hook'
    create_test_webhooks(user=user, url=url)
    emit_mock = mocker.patch('src.logs.events.mixins.emit')
    webhooks_unsubscribed_mock = mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.webhooks_unsubscribed',
    )
    service = WebhookService(user=user)

    # act
    service.unsubscribe()

    # assert
    emit_mock.assert_called_once_with(
        EventName.WEBHOOK_UNSUBSCRIBE,
        account_id=user.account_id,
        actor=Actor(
            type=ActorType.USER,
            id=user.id,
            email=user.email,
        ),
        event_object=EventObject(type=EventObjectType.WEBHOOK),
        payload={'url': url, 'event': ALL_EVENTS},
    )
    webhooks_unsubscribed_mock.assert_called_once_with()


def test_unsubscribe__two_targets__emit_an_event_per_target(mocker):

    """ Subscriptions of one account may point at different
        receivers: each address that stops receiving is an event. """

    # arrange
    user = create_test_owner()
    first_url = 'https://93.184.216.34/first'
    second_url = 'https://93.184.216.34/second'
    create_test_webhook(
        user=user,
        event=HookEvent.WORKFLOW_STARTED,
        url=first_url,
    )
    create_test_webhook(
        user=user,
        event=HookEvent.WORKFLOW_COMPLETED,
        url=second_url,
    )
    emit_mock = mocker.patch('src.logs.events.mixins.emit')
    webhooks_unsubscribed_mock = mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.webhooks_unsubscribed',
    )
    service = WebhookService(user=user)

    # act
    service.unsubscribe()

    # assert
    assert emit_mock.call_count == 2
    emit_mock.assert_has_calls([
        mocker.call(
            EventName.WEBHOOK_UNSUBSCRIBE,
            account_id=user.account_id,
            actor=Actor(
                type=ActorType.USER,
                id=user.id,
                email=user.email,
            ),
            event_object=EventObject(type=EventObjectType.WEBHOOK),
            payload={'url': first_url, 'event': ALL_EVENTS},
        ),
        mocker.call(
            EventName.WEBHOOK_UNSUBSCRIBE,
            account_id=user.account_id,
            actor=Actor(
                type=ActorType.USER,
                id=user.id,
                email=user.email,
            ),
            event_object=EventObject(type=EventObjectType.WEBHOOK),
            payload={'url': second_url, 'event': ALL_EVENTS},
        ),
    ])
    webhooks_unsubscribed_mock.assert_called_once_with()


def test_unsubscribe__no_subscriptions__no_event(mocker):

    # arrange
    user = create_test_owner()
    emit_mock = mocker.patch('src.logs.events.mixins.emit')
    webhooks_unsubscribed_mock = mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.webhooks_unsubscribed',
    )
    service = WebhookService(user=user)

    # act
    service.unsubscribe()

    # assert
    emit_mock.assert_not_called()
    webhooks_unsubscribed_mock.assert_called_once_with()


def test_unsubscribe_event__single_event__emit_webhook_unsubscribe(mocker):

    # arrange
    user = create_test_owner()
    event = HookEvent.WORKFLOW_STARTED
    url = 'https://93.184.216.34/hook'
    create_test_webhook(user=user, event=event, url=url)
    emit_mock = mocker.patch('src.logs.events.mixins.emit')
    webhooks_unsubscribed_mock = mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.webhooks_unsubscribed',
    )
    service = WebhookService(user=user)

    # act
    service.unsubscribe_event(event=event)

    # assert
    emit_mock.assert_called_once_with(
        EventName.WEBHOOK_UNSUBSCRIBE,
        account_id=user.account_id,
        actor=Actor(
            type=ActorType.USER,
            id=user.id,
            email=user.email,
        ),
        event_object=EventObject(type=EventObjectType.WEBHOOK),
        payload={'url': url, 'event': event},
    )
    webhooks_unsubscribed_mock.assert_called_once_with()


def test_unsubscribe_event__other_subscriptions_remain__emit_only(mocker):

    """ The integration stays on while another event is still
        subscribed: the event is about the one address that stops. """

    # arrange
    user = create_test_owner()
    event = HookEvent.WORKFLOW_STARTED
    url = 'https://93.184.216.34/hook'
    create_test_webhook(user=user, event=event, url=url)
    create_test_webhook(
        user=user,
        event=HookEvent.WORKFLOW_COMPLETED,
        url=url,
    )
    emit_mock = mocker.patch('src.logs.events.mixins.emit')
    webhooks_unsubscribed_mock = mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.webhooks_unsubscribed',
    )
    service = WebhookService(user=user)

    # act
    service.unsubscribe_event(event=event)

    # assert
    emit_mock.assert_called_once_with(
        EventName.WEBHOOK_UNSUBSCRIBE,
        account_id=user.account_id,
        actor=Actor(
            type=ActorType.USER,
            id=user.id,
            email=user.email,
        ),
        event_object=EventObject(type=EventObjectType.WEBHOOK),
        payload={'url': url, 'event': event},
    )
    webhooks_unsubscribed_mock.assert_not_called()


def test_unsubscribe_event__no_subscription__no_event(mocker):

    # arrange
    user = create_test_owner()
    emit_mock = mocker.patch('src.logs.events.mixins.emit')
    webhooks_unsubscribed_mock = mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.webhooks_unsubscribed',
    )
    service = WebhookService(user=user)

    # act
    service.unsubscribe_event(event=HookEvent.WORKFLOW_STARTED)

    # assert
    emit_mock.assert_not_called()
    webhooks_unsubscribed_mock.assert_called_once_with()
