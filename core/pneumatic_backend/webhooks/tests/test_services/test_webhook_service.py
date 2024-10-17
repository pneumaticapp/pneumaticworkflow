import pytest
from pneumatic_backend.processes.tests.fixtures import create_test_user
from pneumatic_backend.webhooks.tests.fixtures import (
    create_test_webhooks,
    create_test_webhook,
)
from pneumatic_backend.webhooks.models import WebHook
from pneumatic_backend.webhooks.services import WebhookService
from pneumatic_backend.webhooks import exceptions
from pneumatic_backend.webhooks.messages import MSG_WH_0001
from pneumatic_backend.processes.api_v2.views.template import (
    TemplateIntegrationsService
)

pytestmark = pytest.mark.django_db


def test_validate_event__ok(mocker):

    # arrange
    user = create_test_user()
    event = 'event'
    events_mock = mocker.patch(
        'pneumatic_backend.webhooks.services.WebhookService._get_events',
        return_value=(event,)
    )
    service = WebhookService(user=user)

    # act
    service._validate_event(event)

    # assert
    events_mock.assert_called_once()


def test_validate_event__invalid_event__raise_exception(mocker):

    # arrange
    event = 'event'
    not_existent_event = 'not_existent_event'
    events_mock = mocker.patch(
        'pneumatic_backend.webhooks.services.WebhookService._get_events',
        return_value=(event,)
    )
    user = create_test_user()
    service = WebhookService(user=user)

    # act
    with pytest.raises(exceptions.InvalidEventException) as ex:
        service._validate_event(not_existent_event)

    # assert
    events_mock.assert_called_once()
    assert ex.value.message == MSG_WH_0001


def test_unsubscribe__ok(mocker):

    # arrange
    user = create_test_user()
    account = user.account
    user_2 = create_test_user(email='test@test.test')
    account_2 = user_2.account
    create_test_webhooks(user)
    create_test_webhooks(user_2)
    service_init_mock = mocker.patch.object(
        TemplateIntegrationsService,
        attribute='__init__',
        return_value=None
    )
    webhooks_unsubscribed_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.webhooks_unsubscribed'
    )
    service = WebhookService(user=user)

    # act
    service.unsubscribe()

    # assert
    assert not account.webhook_set.exists()
    assert account_2.webhook_set.exists()
    service_init_mock.assert_called_once_with(
        account=user.account,
        is_superuser=False,
        user=user
    )
    webhooks_unsubscribed_mock.assert_called_once_with()


def test_unsubscribe_event__ok(mocker):

    # arrange
    user = create_test_user()
    user_2 = create_test_user(email='test@test.test')
    event_1 = 'event_1'
    event_2 = 'event_2'
    hook_1 = create_test_webhook(user=user, event=event_1)
    hook_2 = create_test_webhook(user=user, event=event_2)
    hook_3 = create_test_webhook(user=user_2, event=event_1)
    events_mock = mocker.patch(
        'pneumatic_backend.webhooks.services.WebhookService._validate_event'
    )
    webhooks_unsubscribed_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.webhooks_unsubscribed'
    )
    service = WebhookService(user=user)

    # act
    service.unsubscribe_event(event=event_1)

    # assert
    events_mock.assert_called_once_with(event_1)
    assert not WebHook.objects.filter(id=hook_1.id).exists()
    assert WebHook.objects.filter(id=hook_2.id).exists()
    assert WebHook.objects.filter(id=hook_3.id).exists()
    webhooks_unsubscribed_mock.assert_not_called()


def test_unsubscribe_event__last_event__ok(mocker):

    # arrange
    user = create_test_user()
    event_1 = 'event_1'
    hook_1 = create_test_webhook(user=user, event=event_1)
    events_mock = mocker.patch(
        'pneumatic_backend.webhooks.services.WebhookService._validate_event'
    )
    service_init_mock = mocker.patch.object(
        TemplateIntegrationsService,
        attribute='__init__',
        return_value=None
    )
    webhooks_unsubscribed_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.webhooks_unsubscribed'
    )
    service = WebhookService(user=user)

    # act
    service.unsubscribe_event(event=event_1)

    # assert
    events_mock.assert_called_once_with(event_1)
    assert not WebHook.objects.filter(id=hook_1.id).exists()
    service_init_mock.assert_called_once_with(
        account=user.account,
        is_superuser=False,
        user=user
    )
    webhooks_unsubscribed_mock.assert_called_once_with()


def test_subscribe_event__create__ok(mocker):

    # arrange
    user = create_test_user()
    event_1 = 'event_1'
    events_mock = mocker.patch(
        'pneumatic_backend.webhooks.services.WebhookService._validate_event'
    )
    analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'accounts_webhooks_subscribed'
    )
    url = 'http://test_2.test'
    service_init_mock = mocker.patch.object(
        TemplateIntegrationsService,
        attribute='__init__',
        return_value=None
    )
    webhooks_subscribed_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.webhooks_subscribed'
    )
    service = WebhookService(user=user)

    # act
    service.subscribe_event(
        url=url,
        event=event_1
    )

    # assert
    events_mock.assert_called_once_with(event_1)
    assert WebHook.objects.filter(
        event=event_1,
        target=url,
        user=user,
        account=user.account
    ).exists()
    service_init_mock.assert_called_once_with(
        account=user.account,
        is_superuser=False,
        user=user
    )
    webhooks_subscribed_mock.assert_called_once_with()
    analytics_mock.assert_called_once_with(
        user=user,
        is_superuser=False
    )


def test_subscribe_event__update__ok(mocker):

    # arrange
    user = create_test_user()
    event_1 = 'event_1'
    events_mock = mocker.patch(
        'pneumatic_backend.webhooks.services.WebhookService._validate_event'
    )
    url = 'http://test_2.test'
    hook = create_test_webhook(
        user=user,
        event=event_1
    )
    service_init_mock = mocker.patch.object(
        TemplateIntegrationsService,
        attribute='__init__',
        return_value=None
    )
    webhooks_subscribed_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.webhooks_subscribed'
    )
    analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'accounts_webhooks_subscribed'
    )
    service = WebhookService(user=user)

    # act
    service.subscribe_event(
        url=url,
        event=event_1
    )

    # assert
    events_mock.assert_called_once_with(event_1)
    hook.refresh_from_db()
    assert hook.target == url
    service_init_mock.assert_called_once_with(
        account=user.account,
        is_superuser=False,
        user=user
    )
    webhooks_subscribed_mock.assert_called_once_with()
    analytics_mock.assert_not_called()


def test_get_event_url__existent__ok(mocker):

    # arrange
    user = create_test_user()
    event_1 = 'event_1'
    events_mock = mocker.patch(
        'pneumatic_backend.webhooks.services.WebhookService._validate_event'
    )
    hook = create_test_webhook(
        user=user,
        event=event_1
    )
    service = WebhookService(user=user)

    # act
    url = service.get_event_url(event=event_1)

    # assert
    events_mock.assert_called_once_with(event_1)
    assert hook.target == url


def test_get_event_url__not_existent__return_none(mocker):

    # arrange
    user = create_test_user()
    event_1 = 'event_1'
    event_2 = 'event_2'
    events_mock = mocker.patch(
        'pneumatic_backend.webhooks.services.WebhookService._validate_event'
    )
    create_test_webhook(
        user=user,
        event=event_1
    )
    service = WebhookService(user=user)

    # act
    url = service.get_event_url(event=event_2)

    # assert
    events_mock.assert_called_once_with(event_2)
    assert url is None


def test_get_events__ok(mocker):

    # arrange
    user = create_test_user()
    event_1 = 'event_1'
    event_2 = 'event_2'
    events_mock = mocker.patch(
        'pneumatic_backend.webhooks.services.WebhookService._get_events',
        return_value={event_1, event_2}
    )
    hook = create_test_webhook(
        user=user,
        event=event_1
    )
    service = WebhookService(user=user)

    # act
    events = service.get_events()

    # assert
    assert len(events) == 2
    for event in events:
        if event['event'] == event_1:
            assert event['url'] == hook.target
        else:
            assert event['url'] is None
    events_mock.assert_called_once()


def test_get_private_events__ok():

    # arrange
    user = create_test_user()
    service = WebhookService(user=user)

    # act
    events = service._get_events()

    # assert
    assert events == {
        'workflow_completed',
        'workflow_started',
        'task_completed_v2',
        'task_returned'
    }


def test_subscribe__create__ok(mocker):

    # arrange
    user = create_test_user()
    account = user.account
    url = 'http://test.test'
    event_1 = 'event_1'
    event_2 = 'event_2'
    events_mock = mocker.patch(
        'pneumatic_backend.webhooks.services.WebhookService._get_events',
        return_value=(event_1, event_2)
    )
    service_init_mock = mocker.patch.object(
        TemplateIntegrationsService,
        attribute='__init__',
        return_value=None
    )
    webhooks_subscribed_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.webhooks_subscribed'
    )
    analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'accounts_webhooks_subscribed'
    )
    service = WebhookService(user=user)

    # act
    service.subscribe(url=url)

    # assert
    assert account.webhook_set.count() == 2
    assert account.webhook_set.filter(
        account_id=account.id,
        user_id=user.id,
        event=event_1,
        target=url
    ).exists()
    assert account.webhook_set.filter(
        account_id=account.id,
        user_id=user.id,
        event=event_2,
        target=url
    ).exists()
    events_mock.assert_called_once()
    service_init_mock.assert_called_once_with(
        account=user.account,
        is_superuser=False,
        user=user
    )
    webhooks_subscribed_mock.assert_called_once_with()
    analytics_mock.assert_called_once_with(
        user=user,
        is_superuser=False
    )


def test_subscribe__recreate__ok(mocker):

    # arrange
    user = create_test_user()
    account = user.account
    url = 'http://test2.test'
    create_test_webhooks(user)
    event = 'event'
    events_mock = mocker.patch(
        'pneumatic_backend.webhooks.services.WebhookService._get_events',
        return_value=(event,)
    )
    service_init_mock = mocker.patch.object(
        TemplateIntegrationsService,
        attribute='__init__',
        return_value=None
    )
    webhooks_subscribed_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.webhooks_subscribed'
    )
    analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'accounts_webhooks_subscribed'
    )
    service = WebhookService(user=user)

    # act
    service.subscribe(url=url)

    # assert
    assert account.webhook_set.count() == 1
    assert account.webhook_set.filter(
        account_id=account.id,
        user_id=user.id,
        event=event,
        target=url
    ).exists()
    events_mock.assert_called_once()
    service_init_mock.assert_called_once_with(
        account=user.account,
        is_superuser=False,
        user=user
    )
    webhooks_subscribed_mock.assert_called_once_with()
    analytics_mock.assert_called_once_with(
        user=user,
        is_superuser=False
    )
