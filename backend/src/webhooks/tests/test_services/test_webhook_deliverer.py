import json

import pytest
import requests
from django.core.serializers.json import DjangoJSONEncoder

from src.logs.enums import (
    AccountEventStatus,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
)
from src.utils.logging import SentryLogLevel
from src.webhooks.enums import HookEvent
from src.webhooks.services import (
    WEBHOOK_TIMEOUT,
    WebhookDeliverer,
)
from src.webhooks.tests.fixtures import (
    create_test_webhook,
)

pytestmark = pytest.mark.django_db


def test_send__ok(mocker):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    event = HookEvent.WORKFLOW_STARTED
    webhook = create_test_webhook(user=user, event=event)
    payload = {'workflow': 'value'}
    response_mock = mocker.Mock(ok=True, status_code=204)
    post_mock = mocker.patch(
        'src.webhooks.services.requests.post',
        return_value=response_mock,
    )
    webhook_log_mock = mocker.patch(
        'src.webhooks.services.AccountLogService.webhook',
    )
    capture_sentry_mock = mocker.patch(
        'src.webhooks.services.capture_sentry_message',
    )
    service = WebhookDeliverer()

    # act
    service.send(
        event=event,
        user_id=user.id,
        account_id=account.id,
        payload=payload,
    )

    # assert
    post_mock.assert_called_once_with(
        url=webhook.target,
        data=json.dumps(
            {
                'hook': {
                    'id': webhook.id,
                    'event': webhook.event,
                    'target': webhook.target,
                },
                'workflow': 'value',
            },
            cls=DjangoJSONEncoder,
        ),
        headers={'Content-Type': 'application/json'},
        timeout=WEBHOOK_TIMEOUT,
    )
    webhook_log_mock.assert_called_once_with(
        title=f'Webhook: {event}',
        path=webhook.target,
        request_data={
            'hook': {
                'id': webhook.id,
                'event': event,
                'target': webhook.target,
            },
            'workflow': 'value',
        },
        account_id=account.id,
        status=AccountEventStatus.SUCCESS,
        http_status=204,
        response_data={},
        user_id=user.id,
    )
    capture_sentry_mock.assert_not_called()


def test_send__webhook_with_another_event__skip(mocker):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    create_test_webhook(user=user, event=HookEvent.WORKFLOW_STARTED)
    payload = {'workflow': 'value'}
    post_mock = mocker.patch('src.webhooks.services.requests.post')
    webhook_log_mock = mocker.patch(
        'src.webhooks.services.AccountLogService.webhook',
    )
    service = WebhookDeliverer()

    # act
    service.send(
        event=HookEvent.WORKFLOW_COMPLETED,
        user_id=user.id,
        account_id=account.id,
        payload=payload,
    )

    # assert
    post_mock.assert_not_called()
    webhook_log_mock.assert_not_called()


def test_send__webhook_with_another_account__skip(mocker):

    # arrange
    another_account = create_test_account()
    user = create_test_owner()
    event = HookEvent.WORKFLOW_STARTED
    create_test_webhook(user=user, event=event)
    payload = {'workflow': 'value'}
    post_mock = mocker.patch('src.webhooks.services.requests.post')
    webhook_log_mock = mocker.patch(
        'src.webhooks.services.AccountLogService.webhook',
    )
    service = WebhookDeliverer()

    # act
    service.send(
        event=event,
        user_id=user.id,
        account_id=another_account.id,
        payload=payload,
    )

    # assert
    post_mock.assert_not_called()
    webhook_log_mock.assert_not_called()


def test_send__connection_error__create_log(mocker):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    event = HookEvent.WORKFLOW_STARTED
    webhook = create_test_webhook(user=user, event=event)
    payload = {'workflow': 'value'}
    post_mock = mocker.patch(
        'src.webhooks.services.requests.post',
        side_effect=requests.ConnectionError('=('),
    )
    webhook_log_mock = mocker.patch(
        'src.webhooks.services.AccountLogService.webhook',
    )
    capture_sentry_mock = mocker.patch(
        'src.webhooks.services.capture_sentry_message',
    )
    service = WebhookDeliverer()

    # act
    with pytest.raises(requests.ConnectionError) as ex:
        service.send(
            event=event,
            user_id=user.id,
            account_id=account.id,
            payload=payload,
        )

    # assert
    assert str(ex.value) == '=('
    post_mock.assert_called_once_with(
        url=webhook.target,
        data=json.dumps(
            {
                'hook': {
                    'id': webhook.id,
                    'event': webhook.event,
                    'target': webhook.target,
                },
                'workflow': 'value',
            },
            cls=DjangoJSONEncoder,
        ),
        headers={'Content-Type': 'application/json'},
        timeout=WEBHOOK_TIMEOUT,
    )
    webhook_log_mock.assert_called_once_with(
        title=f'Webhook: {event}',
        path=webhook.target,
        request_data={
            'hook': {
                'id': webhook.id,
                'event': event,
                'target': webhook.target,
            },
            'workflow': 'value',
        },
        account_id=account.id,
        status=AccountEventStatus.FAILED,
        http_status=None,
        response_data={'ConnectionError': '=('},
        user_id=user.id,
    )
    capture_sentry_mock.assert_called_once_with(
        message='HttpException sending webhook',
        data={
            'request_url': webhook.target,
            'exception': '=(',
        },
        level=SentryLogLevel.INFO,
    )


def test_send__timeout__create_log(mocker):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    event = HookEvent.WORKFLOW_STARTED
    webhook = create_test_webhook(user=user, event=event)
    payload = {'workflow': 'value'}
    post_mock = mocker.patch(
        'src.webhooks.services.requests.post',
        side_effect=requests.Timeout('too slow'),
    )
    webhook_log_mock = mocker.patch(
        'src.webhooks.services.AccountLogService.webhook',
    )
    capture_sentry_mock = mocker.patch(
        'src.webhooks.services.capture_sentry_message',
    )
    service = WebhookDeliverer()

    # act
    with pytest.raises(requests.Timeout) as ex:
        service.send(
            event=event,
            user_id=user.id,
            account_id=account.id,
            payload=payload,
        )

    # assert
    assert str(ex.value) == 'too slow'
    post_mock.assert_called_once_with(
        url=webhook.target,
        data=json.dumps(
            {
                'hook': {
                    'id': webhook.id,
                    'event': webhook.event,
                    'target': webhook.target,
                },
                'workflow': 'value',
            },
            cls=DjangoJSONEncoder,
        ),
        headers={'Content-Type': 'application/json'},
        timeout=WEBHOOK_TIMEOUT,
    )
    webhook_log_mock.assert_called_once_with(
        title=f'Webhook: {event}',
        path=webhook.target,
        request_data={
            'hook': {
                'id': webhook.id,
                'event': event,
                'target': webhook.target,
            },
            'workflow': 'value',
        },
        account_id=account.id,
        status=AccountEventStatus.FAILED,
        http_status=None,
        response_data={'ConnectionError': 'too slow'},
        user_id=user.id,
    )
    capture_sentry_mock.assert_called_once_with(
        message='HttpException sending webhook',
        data={
            'request_url': webhook.target,
            'exception': 'too slow',
        },
        level=SentryLogLevel.INFO,
    )


def test_send__bad_request_content_type_json__ok(mocker):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    event = HookEvent.WORKFLOW_STARTED
    webhook = create_test_webhook(user=user, event=event)
    payload = {'workflow': 'value'}
    bad_response_data = {'some': 'error'}
    response_mock = mocker.Mock(
        ok=False,
        status_code=400,
        headers={'content-type': 'application/json'},
        json=mocker.Mock(return_value=bad_response_data),
    )
    post_mock = mocker.patch(
        'src.webhooks.services.requests.post',
        return_value=response_mock,
    )
    webhook_log_mock = mocker.patch(
        'src.webhooks.services.AccountLogService.webhook',
    )
    capture_sentry_mock = mocker.patch(
        'src.webhooks.services.capture_sentry_message',
    )
    service = WebhookDeliverer()

    # act
    service.send(
        event=event,
        user_id=user.id,
        account_id=account.id,
        payload=payload,
    )

    # assert
    post_mock.assert_called_once_with(
        url=webhook.target,
        data=json.dumps(
            {
                'hook': {
                    'id': webhook.id,
                    'event': webhook.event,
                    'target': webhook.target,
                },
                'workflow': 'value',
            },
            cls=DjangoJSONEncoder,
        ),
        headers={'Content-Type': 'application/json'},
        timeout=WEBHOOK_TIMEOUT,
    )
    webhook_log_mock.assert_called_once_with(
        title=f'Webhook: {event}',
        path=webhook.target,
        request_data={
            'hook': {
                'id': webhook.id,
                'event': event,
                'target': webhook.target,
            },
            'workflow': 'value',
        },
        account_id=account.id,
        status=AccountEventStatus.FAILED,
        http_status=400,
        response_data={
            'response': {
                'request_url': webhook.target,
                'response_status': 400,
                'response_json': bad_response_data,
            },
        },
        user_id=user.id,
    )
    capture_sentry_mock.assert_called_once_with(
        message='Error sending webhook',
        data={
            'request_url': webhook.target,
            'response_status': 400,
            'response_json': bad_response_data,
        },
        level=SentryLogLevel.INFO,
    )


def test_send__permission_denied_type_text__ok(mocker):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    event = HookEvent.WORKFLOW_STARTED
    webhook = create_test_webhook(user=user, event=event)
    payload = {'workflow': 'value'}
    bad_response_text = 'Error text or html'
    response_mock = mocker.Mock(
        ok=False,
        status_code=403,
        headers={'content-type': 'text/html'},
        text=bad_response_text,
    )
    post_mock = mocker.patch(
        'src.webhooks.services.requests.post',
        return_value=response_mock,
    )
    webhook_log_mock = mocker.patch(
        'src.webhooks.services.AccountLogService.webhook',
    )
    capture_sentry_mock = mocker.patch(
        'src.webhooks.services.capture_sentry_message',
    )
    service = WebhookDeliverer()

    # act
    service.send(
        event=event,
        user_id=user.id,
        account_id=account.id,
        payload=payload,
    )

    # assert
    post_mock.assert_called_once_with(
        url=webhook.target,
        data=json.dumps(
            {
                'hook': {
                    'id': webhook.id,
                    'event': webhook.event,
                    'target': webhook.target,
                },
                'workflow': 'value',
            },
            cls=DjangoJSONEncoder,
        ),
        headers={'Content-Type': 'application/json'},
        timeout=WEBHOOK_TIMEOUT,
    )
    webhook_log_mock.assert_called_once_with(
        title=f'Webhook: {event}',
        path=webhook.target,
        request_data={
            'hook': {
                'id': webhook.id,
                'event': event,
                'target': webhook.target,
            },
            'workflow': 'value',
        },
        account_id=account.id,
        status=AccountEventStatus.FAILED,
        http_status=403,
        response_data={
            'response': {
                'request_url': webhook.target,
                'response_status': 403,
                'response_text': bad_response_text,
            },
        },
        user_id=user.id,
    )
    capture_sentry_mock.assert_called_once_with(
        message='Error sending webhook',
        data={
            'request_url': webhook.target,
            'response_status': 403,
            'response_text': bad_response_text,
        },
        level=SentryLogLevel.INFO,
    )


def test_send__not_found__ok(mocker):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    event = HookEvent.WORKFLOW_STARTED
    webhook = create_test_webhook(user=user, event=event)
    payload = {'workflow': 'value'}
    response_mock = mocker.Mock(
        ok=False,
        status_code=404,
        headers={'content-type': 'text/html'},
        text='Error text or html',
    )
    post_mock = mocker.patch(
        'src.webhooks.services.requests.post',
        return_value=response_mock,
    )
    webhook_log_mock = mocker.patch(
        'src.webhooks.services.AccountLogService.webhook',
    )
    capture_sentry_mock = mocker.patch(
        'src.webhooks.services.capture_sentry_message',
    )
    service = WebhookDeliverer()

    # act
    service.send(
        event=event,
        user_id=user.id,
        account_id=account.id,
        payload=payload,
    )

    # assert
    post_mock.assert_called_once_with(
        url=webhook.target,
        data=json.dumps(
            {
                'hook': {
                    'id': webhook.id,
                    'event': webhook.event,
                    'target': webhook.target,
                },
                'workflow': 'value',
            },
            cls=DjangoJSONEncoder,
        ),
        headers={'Content-Type': 'application/json'},
        timeout=WEBHOOK_TIMEOUT,
    )
    webhook_log_mock.assert_called_once_with(
        title=f'Webhook: {event}',
        path=webhook.target,
        request_data={
            'hook': {
                'id': webhook.id,
                'event': event,
                'target': webhook.target,
            },
            'workflow': 'value',
        },
        account_id=account.id,
        status=AccountEventStatus.FAILED,
        http_status=404,
        response_data={
            'response': {
                'request_url': webhook.target,
                'response_status': 404,
            },
        },
        user_id=user.id,
    )
    capture_sentry_mock.assert_called_once_with(
        message='Error sending webhook',
        data={
            'request_url': webhook.target,
            'response_status': 404,
        },
        level=SentryLogLevel.INFO,
    )


def test_send__internal_server_error__raise_exception(mocker):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    event = HookEvent.WORKFLOW_STARTED
    webhook = create_test_webhook(user=user, event=event)
    payload = {'workflow': 'value'}
    response_mock = mocker.Mock(
        ok=False,
        status_code=500,
        headers={'content-type': 'text/html'},
        text='internal server error',
    )
    post_mock = mocker.patch(
        'src.webhooks.services.requests.post',
        return_value=response_mock,
    )
    webhook_log_mock = mocker.patch(
        'src.webhooks.services.AccountLogService.webhook',
    )
    capture_sentry_mock = mocker.patch(
        'src.webhooks.services.capture_sentry_message',
    )
    service = WebhookDeliverer()

    # act
    with pytest.raises(ConnectionError) as ex:
        service.send(
            event=event,
            user_id=user.id,
            account_id=account.id,
            payload=payload,
        )

    # assert
    assert str(ex.value) == 'Error sending webhook (500)'
    post_mock.assert_called_once_with(
        url=webhook.target,
        data=json.dumps(
            {
                'hook': {
                    'id': webhook.id,
                    'event': webhook.event,
                    'target': webhook.target,
                },
                'workflow': 'value',
            },
            cls=DjangoJSONEncoder,
        ),
        headers={'Content-Type': 'application/json'},
        timeout=WEBHOOK_TIMEOUT,
    )
    webhook_log_mock.assert_called_once_with(
        title=f'Webhook: {event}',
        path=webhook.target,
        request_data={
            'hook': {
                'id': webhook.id,
                'event': event,
                'target': webhook.target,
            },
            'workflow': 'value',
        },
        account_id=account.id,
        status=AccountEventStatus.FAILED,
        http_status=500,
        response_data={
            'response': {
                'request_url': webhook.target,
                'response_status': 500,
                'response_text': 'internal server error',
            },
        },
        user_id=user.id,
    )
    capture_sentry_mock.assert_called_once_with(
        message='Error sending webhook',
        data={
            'request_url': webhook.target,
            'response_status': 500,
            'response_text': 'internal server error',
        },
        level=SentryLogLevel.INFO,
    )
