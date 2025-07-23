import pytest
from pneumatic_backend.processes.tests.fixtures import create_test_user
from pneumatic_backend.webhooks import exceptions
from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.webhooks.views.events import (
    WebhookService,
)

pytestmark = pytest.mark.django_db


def test_list__ok(api_client, mocker):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    data = 'some_data'
    service_init_mock = mocker.patch.object(
        WebhookService,
        attribute='__init__',
        return_value=None
    )
    service_mock = mocker.patch(
        'pneumatic_backend.webhooks.views.events.WebhookService'
        '.get_events',
        return_value=data
    )

    # act
    response = api_client.get('/webhooks/events')

    # assert
    assert response.status_code == 200
    assert response.data == data
    service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False
    )
    service_mock.assert_called_once()


def test_retrieve__ok(api_client, mocker):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    url = 'some url'
    event = 'event_1'
    service_init_mock = mocker.patch.object(
        WebhookService,
        attribute='__init__',
        return_value=None
    )
    service_mock = mocker.patch(
        'pneumatic_backend.webhooks.views.events.WebhookService'
        '.get_event_url',
        return_value=url
    )

    # act
    response = api_client.get(f'/webhooks/events/{event}')

    # assert
    assert response.status_code == 200
    assert response.data['url'] == url
    service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False
    )
    service_mock.assert_called_once_with(event=event)


def test_retrieve__not_admin__permission_denied(api_client):

    # arrange
    user = create_test_user(
        is_admin=False,
        is_account_owner=False
    )
    api_client.token_authenticate(user)
    event = 'event_1'

    # act
    response = api_client.get(f'/webhooks/events/{event}')

    # assert
    assert response.status_code == 403


def test_retrieve__not_auth__permission_denied(api_client):

    # arrange
    event = 'event_1'

    # act
    response = api_client.get(f'/webhooks/events/{event}')

    # assert
    assert response.status_code == 401


def test_retrieve__invalid_event__not_found(api_client, mocker):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    event = 'event_1'
    service_init_mock = mocker.patch.object(
        WebhookService,
        attribute='__init__',
        return_value=None
    )
    service_mock = mocker.patch(
        'pneumatic_backend.webhooks.views.events.WebhookService'
        '.get_event_url',
        side_effect=exceptions.InvalidEventException
    )

    # act
    response = api_client.get(f'/webhooks/events/{event}')

    # assert
    assert response.status_code == 404
    service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False
    )
    service_mock.assert_called_once_with(event=event)


def test_subscribe__ok(api_client, mocker):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    url = 'https://test.test'
    event = 'event_1'
    service_init_mock = mocker.patch.object(
        WebhookService,
        attribute='__init__',
        return_value=None
    )
    service_mock = mocker.patch(
        'pneumatic_backend.webhooks.views.events.WebhookService'
        '.subscribe_event'
    )

    # act
    response = api_client.post(
        path=f'/webhooks/events/{event}/subscribe',
        data={'url': url}
    )

    # assert
    assert response.status_code == 204
    service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False
    )
    service_mock.assert_called_once_with(
        event=event,
        url=url
    )


def test_subscribe__invalid_event__not_found(api_client, mocker):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    url = 'https://test.test'
    event = 'event_1'
    service_init_mock = mocker.patch.object(
        WebhookService,
        attribute='__init__',
        return_value=None
    )
    service_mock = mocker.patch(
        'pneumatic_backend.webhooks.views.events.WebhookService'
        '.subscribe_event',
        side_effect=exceptions.InvalidEventException
    )

    # act
    response = api_client.post(
        path=f'/webhooks/events/{event}/subscribe',
        data={'url': url}
    )

    # assert
    assert response.status_code == 404
    service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False
    )
    service_mock.assert_called_once_with(
        event=event,
        url=url
    )


def test_subscribe__invalid_url__validation__error(api_client, mocker):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    url = 'some url'
    event = 'event_1'
    service_mock = mocker.patch(
        'pneumatic_backend.webhooks.views.events.WebhookService'
        '.subscribe_event'
    )

    # act
    response = api_client.post(
        path=f'/webhooks/events/{event}/subscribe',
        data={'url': url}
    )

    # assert
    assert response.status_code == 400
    message = 'Enter a valid URL.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'url'
    service_mock.assert_not_called()


def test_unsubscribe__ok(api_client, mocker):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    event = 'event_1'
    service_mock = mocker.patch(
        'pneumatic_backend.webhooks.views.events.WebhookService'
        '.unsubscribe_event'
    )
    service_init_mock = mocker.patch.object(
        WebhookService,
        attribute='__init__',
        return_value=None
    )

    # act
    response = api_client.post(
        f'/webhooks/events/{event}/unsubscribe'
    )

    # assert
    assert response.status_code == 204
    service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False
    )
    service_mock.assert_called_once_with(event=event)


def test_unsubscribe__invalid_event__not_found(api_client, mocker):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    event = 'event_1'
    service_init_mock = mocker.patch.object(
        WebhookService,
        attribute='__init__',
        return_value=None
    )
    service_mock = mocker.patch(
        'pneumatic_backend.webhooks.views.events.WebhookService'
        '.unsubscribe_event',
        side_effect=exceptions.InvalidEventException
    )

    # act
    response = api_client.post(
        f'/webhooks/events/{event}/unsubscribe'
    )

    # assert
    assert response.status_code == 404
    service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False
    )
    service_mock.assert_called_once_with(event=event)
