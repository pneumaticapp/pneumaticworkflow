import pytest


pytestmark = pytest.mark.django_db


def test_buffer_create__ok(api_client, mocker):

    # arrange
    data = {'some': 'hook data'}
    service_mock = mocker.patch(
        'pneumatic_backend.webhooks.views.buffer.WebhookBufferService.push'
    )

    # act
    response = api_client.post(
        path='/webhooks/buffer',
        data=data
    )

    # assert
    assert response.status_code == 204
    service_mock.assert_called_once_with(data)


def test_buffer_create__env_prod__permission_denied(api_client, mocker):

    # arrange
    data = {'some': 'hook data'}
    permission_mock = mocker.patch(
        'pneumatic_backend.generics.permissions.StagingPermission.'
        'has_permission',
        return_value=False
    )

    # act
    response = api_client.post(
        path='/webhooks/buffer',
        data=data
    )

    # assert
    assert response.status_code == 401
    permission_mock.assert_called_once()


def test_buffer_list__ok(api_client, mocker):

    # arrange
    data = [{'some': 'hook data'}]
    service_mock = mocker.patch(
        'pneumatic_backend.webhooks.views.buffer.WebhookBufferService'
        '.get_list',
        return_value=data
    )

    # act
    response = api_client.get('/webhooks/buffer')

    # assert
    assert response.status_code == 200
    assert response.data == data
    service_mock.assert_called_once()


def test_buffer_clear__ok(api_client, mocker):

    # arrange
    service_mock = mocker.patch(
        'pneumatic_backend.webhooks.views.buffer.WebhookBufferService.clear'
    )

    # act
    response = api_client.post('/webhooks/buffer/clear')

    # assert
    assert response.status_code == 204
    service_mock.assert_called_once()
