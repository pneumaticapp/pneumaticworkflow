import pytest

from src.authentication.enums import AuthTokenType
from src.processes.tests.fixtures import create_test_owner
from src.webhooks.enums import HookEvent
from src.webhooks.models import WebHook
from src.webhooks.services import WebhookService
from src.webhooks.tests.fixtures import (
    create_test_webhook,
    create_test_webhooks,
)

pytestmark = pytest.mark.django_db


def test_subscribe__all_events__emit_webhook_subscribe(mocker):

    # arrange
    user = create_test_owner()
    url = 'https://192.0.2.1/hook'
    webhook_subscribed_mock = mocker.patch(
        'src.webhooks.services.AuditEventService.webhook_subscribed',
    )
    webhooks_subscribed_mock = mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.webhooks_subscribed',
    )
    accounts_webhooks_subscribed_mock = mocker.patch(
        'src.analysis.services.AnalyticService.'
        'accounts_webhooks_subscribed',
    )
    service = WebhookService(user=user)

    # act
    service.subscribe(url=url)

    # assert
    webhook_subscribed_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        url=url,
        event='all',
    )
    webhooks_subscribed_mock.assert_called_once_with()
    accounts_webhooks_subscribed_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
    )


def test_subscribe__api_key_auth__emit_api_auth_type(mocker):

    # arrange
    user = create_test_owner()
    url = 'https://192.0.2.1/hook'
    webhook_subscribed_mock = mocker.patch(
        'src.webhooks.services.AuditEventService.webhook_subscribed',
    )
    webhooks_subscribed_mock = mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.webhooks_subscribed',
    )
    accounts_webhooks_subscribed_mock = mocker.patch(
        'src.analysis.services.AnalyticService.'
        'accounts_webhooks_subscribed',
    )
    service = WebhookService(
        user=user,
        auth_type=AuthTokenType.API,
    )

    # act
    service.subscribe(url=url)

    # assert
    webhook_subscribed_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.API,
        url=url,
        event='all',
    )
    webhooks_subscribed_mock.assert_called_once_with()
    accounts_webhooks_subscribed_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
    )


def test_subscribe_event__single_event__emit_webhook_subscribe(mocker):

    # arrange
    user = create_test_owner()
    event = HookEvent.WORKFLOW_STARTED
    url = 'https://192.0.2.1/hook'
    webhook_subscribed_mock = mocker.patch(
        'src.webhooks.services.AuditEventService.webhook_subscribed',
    )
    webhooks_subscribed_mock = mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.webhooks_subscribed',
    )
    accounts_webhooks_subscribed_mock = mocker.patch(
        'src.analysis.services.AnalyticService.'
        'accounts_webhooks_subscribed',
    )
    service = WebhookService(user=user)

    # act
    service.subscribe_event(
        url=url,
        event=event,
    )

    # assert
    webhook_subscribed_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        url=url,
        event=event,
    )
    webhooks_subscribed_mock.assert_called_once_with()
    accounts_webhooks_subscribed_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
    )


def test_unsubscribe__all_events__emit_webhook_unsubscribe(mocker):

    # arrange
    user = create_test_owner()
    url = 'https://192.0.2.1/hook'
    create_test_webhooks(
        user=user,
        url=url,
    )
    webhook_unsubscribed_mock = mocker.patch(
        'src.webhooks.services.AuditEventService.webhook_unsubscribed',
    )
    webhooks_unsubscribed_mock = mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.webhooks_unsubscribed',
    )
    service = WebhookService(user=user)

    # act
    service.unsubscribe()

    # assert
    assert not WebHook.objects.on_account(user.account_id).exists()
    webhook_unsubscribed_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        event='all',
    )
    webhooks_unsubscribed_mock.assert_called_once_with()


def test_unsubscribe__no_subscriptions__event_written(mocker):

    """ The request is the action: it is written whether or not
        there was a hook to remove. """

    # arrange
    user = create_test_owner()
    webhook_unsubscribed_mock = mocker.patch(
        'src.webhooks.services.AuditEventService.webhook_unsubscribed',
    )
    webhooks_unsubscribed_mock = mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.webhooks_unsubscribed',
    )
    service = WebhookService(user=user)

    # act
    service.unsubscribe()

    # assert
    webhook_unsubscribed_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        event='all',
    )
    webhooks_unsubscribed_mock.assert_called_once_with()


def test_unsubscribe_event__single_event__emit_webhook_unsubscribe(mocker):

    # arrange
    user = create_test_owner()
    event = HookEvent.WORKFLOW_STARTED
    url = 'https://192.0.2.1/hook'
    webhook = create_test_webhook(
        user=user,
        event=event,
        url=url,
    )
    webhook_unsubscribed_mock = mocker.patch(
        'src.webhooks.services.AuditEventService.webhook_unsubscribed',
    )
    webhooks_unsubscribed_mock = mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.webhooks_unsubscribed',
    )
    service = WebhookService(user=user)

    # act
    service.unsubscribe_event(event=event)

    # assert
    assert not WebHook.objects.filter(id=webhook.id).exists()
    webhook_unsubscribed_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        event=event,
    )
    webhooks_unsubscribed_mock.assert_called_once_with()


def test_unsubscribe_event__other_subscriptions_remain__emit_only(mocker):

    """ The integration stays on while another event is still
        subscribed: the record is about the one event that stops. """

    # arrange
    user = create_test_owner()
    event = HookEvent.WORKFLOW_STARTED
    url = 'https://192.0.2.1/hook'
    webhook = create_test_webhook(
        user=user,
        event=event,
        url=url,
    )
    remaining_webhook = create_test_webhook(
        user=user,
        event=HookEvent.WORKFLOW_COMPLETED,
        url=url,
    )
    webhook_unsubscribed_mock = mocker.patch(
        'src.webhooks.services.AuditEventService.webhook_unsubscribed',
    )
    webhooks_unsubscribed_mock = mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.webhooks_unsubscribed',
    )
    service = WebhookService(user=user)

    # act
    service.unsubscribe_event(event=event)

    # assert
    assert not WebHook.objects.filter(id=webhook.id).exists()
    assert WebHook.objects.on_account(
        user.account_id,
    ).get().id == remaining_webhook.id
    webhook_unsubscribed_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        event=event,
    )
    webhooks_unsubscribed_mock.assert_not_called()


def test_unsubscribe_event__no_subscription__event_written(mocker):

    # arrange
    user = create_test_owner()
    webhook_unsubscribed_mock = mocker.patch(
        'src.webhooks.services.AuditEventService.webhook_unsubscribed',
    )
    webhooks_unsubscribed_mock = mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.webhooks_unsubscribed',
    )
    service = WebhookService(user=user)

    # act
    service.unsubscribe_event(event=HookEvent.WORKFLOW_STARTED)

    # assert
    webhook_unsubscribed_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        event=HookEvent.WORKFLOW_STARTED,
    )
    webhooks_unsubscribed_mock.assert_called_once_with()
