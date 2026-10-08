import pytest

from src.authentication.enums import AuthTokenType
from src.processes.tests.fixtures import (
    create_test_owner,
    create_test_user,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_subscribe__ok(api_client, mocker):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    url = 'http://test.test'
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
    user = create_test_user()
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
    user = create_test_user(is_admin=False, is_account_owner=False)
    api_client.token_authenticate(user)
    url = 'http://test.test'
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
    user = create_test_user()
    api_client.token_authenticate(user)
    service_mock = mocker.patch(
        'src.webhooks.views.webhooks.WebhookService.unsubscribe',
    )

    # act
    response = api_client.post(path='/webhooks/unsubscribe')

    # assert
    assert response.status_code == 204
    service_mock.assert_called_once()


def test_subscribe__api_key__emit_api_auth_type(api_client, mocker):

    """ The service has no request: the kind of the caller comes
        from the token type the view hands over. """

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user, token_type=AuthTokenType.API)
    webhooks_subscribed_mock = mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.webhooks_subscribed',
    )
    accounts_webhooks_subscribed_mock = mocker.patch(
        'src.analysis.services.AnalyticService.'
        'accounts_webhooks_subscribed',
    )
    webhook_subscribed_mock = mocker.patch(
        'src.webhooks.services.AuditEventService.webhook_subscribed',
    )
    url = 'http://test.test'

    # act
    response = api_client.post(
        path='/webhooks/subscribe',
        data={'url': url},
    )

    # assert
    assert response.status_code == 204
    webhooks_subscribed_mock.assert_called_once_with()
    accounts_webhooks_subscribed_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
    )
    webhook_subscribed_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.API,
        url=url,
        event='all',
    )


def test_subscribe__invalid_url__no_event(api_client, mocker):

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)
    webhooks_subscribed_mock = mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.webhooks_subscribed',
    )
    accounts_webhooks_subscribed_mock = mocker.patch(
        'src.analysis.services.AnalyticService.'
        'accounts_webhooks_subscribed',
    )
    webhook_subscribed_mock = mocker.patch(
        'src.webhooks.services.AuditEventService.webhook_subscribed',
    )
    url = 'undefined'

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
    assert response.data['details']['name'] == 'url'
    assert response.data['details']['reason'] == message
    webhooks_subscribed_mock.assert_not_called()
    accounts_webhooks_subscribed_mock.assert_not_called()
    webhook_subscribed_mock.assert_not_called()
