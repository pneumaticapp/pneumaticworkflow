import pytest
from pneumatic_backend.processes.tests.fixtures import create_test_user
from pneumatic_backend.utils.validation import ErrorCode


pytestmark = pytest.mark.django_db


def test_subscribe__ok(api_client, mocker):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    url = 'http://test.test'
    service_mock = mocker.patch(
        'pneumatic_backend.webhooks.views.webhooks.WebhookService.subscribe'
    )

    # act
    response = api_client.post(
        path='/webhooks/subscribe',
        data={'url': url}
    )

    # assert
    assert response.status_code == 204
    service_mock.assert_called_once_with(url=url)


def test_subscribe__invalid_url__validation_error(api_client, mocker):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    url = 'undefined'
    service_mock = mocker.patch(
        'pneumatic_backend.webhooks.views.webhooks.WebhookService.subscribe'
    )

    # act
    response = api_client.post(
        path='/webhooks/subscribe',
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


def test_subscribe__not_admin__permission_denied(api_client, mocker):

    # arrange
    user = create_test_user(is_admin=False, is_account_owner=False)
    api_client.token_authenticate(user)
    url = 'http://test.test'
    service_mock = mocker.patch(
        'pneumatic_backend.webhooks.views.webhooks.WebhookService.subscribe'
    )

    # act
    response = api_client.post(
        path='/webhooks/subscribe',
        data={'url': url}
    )

    # assert
    assert response.status_code == 403
    service_mock.assert_not_called()


def test_unsubscribe__ok(api_client, mocker):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    service_mock = mocker.patch(
        'pneumatic_backend.webhooks.views.webhooks.WebhookService.unsubscribe'
    )

    # act
    response = api_client.post(path='/webhooks/unsubscribe')

    # assert
    assert response.status_code == 204
    service_mock.assert_called_once()
