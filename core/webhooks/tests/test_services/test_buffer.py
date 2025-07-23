import pytest
from pneumatic_backend.webhooks.services import WebhookBufferService


pytestmark = pytest.mark.django_db


def test_push__add_to_existent_list__ok(mocker):

    # arrange
    webhook_data_1 = {'some': 'data'}
    webhook_data_2 = {'more': 'values'}
    cached_value = [webhook_data_1]
    get_cache_mock = mocker.patch(
        'pneumatic_backend.webhooks.services.WebhookBufferService._get_cache',
        return_value=cached_value
    )
    set_cache_mock = mocker.patch(
        'pneumatic_backend.webhooks.services.WebhookBufferService._set_cache'
    )

    # act
    WebhookBufferService.push(webhook_data_2)

    # assert
    get_cache_mock.assert_called_once_with(default=[])
    set_cache_mock.assert_called_once_with(
        [webhook_data_1, webhook_data_2]
    )


def test_push___ok(mocker):

    # arrange
    webhook_data = {'more': 'values'}
    get_cache_mock = mocker.patch(
        'pneumatic_backend.webhooks.services.WebhookBufferService._get_cache',
        return_value=[]
    )
    set_cache_mock = mocker.patch(
        'pneumatic_backend.webhooks.services.WebhookBufferService._set_cache'
    )

    # act
    WebhookBufferService.push(webhook_data)

    # assert
    get_cache_mock.assert_called_once_with(default=[])
    set_cache_mock.assert_called_once_with([webhook_data])


def test_get_list__ok(mocker):

    # arrange
    cached_data = [
        {'first': 'value'},
        {'last': 'value'}
    ]
    get_cache_mock = mocker.patch(
        'pneumatic_backend.webhooks.services.WebhookBufferService._get_cache',
        return_value=cached_data
    )

    # act
    value = WebhookBufferService.get_list()

    # assert
    get_cache_mock.assert_called_once_with(default=[])
    assert value == [
        {'last': 'value'},
        {'first': 'value'}
    ]


def test_get_list__null_value_in_cache__ok(mocker):

    # arrange
    cached_data = None
    get_cache_mock = mocker.patch(
        'pneumatic_backend.webhooks.services.WebhookBufferService._get_cache',
        return_value=cached_data
    )

    # act
    value = WebhookBufferService.get_list()

    # assert
    get_cache_mock.assert_called_once_with(default=[])
    assert value == []


def test_clear__ok(mocker):

    # arrange
    delete_cache_mock = mocker.patch(
        'pneumatic_backend.webhooks.services.WebhookBufferService.'
        '_delete_cache'
    )

    # act
    WebhookBufferService.clear()

    # assert
    delete_cache_mock.assert_called_once()
