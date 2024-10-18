import pytest
from pneumatic_backend.analytics.tests.fixtures import create_test_user
from pneumatic_backend.analytics.customerio.exceptions import (
    WebhookInvalidData,
    WebhookUserNotFound
)
from pneumatic_backend.analytics.customerio.enums import MetricType

pytestmark = pytest.mark.django_db


class TestWebhooksView:

    def test_unsubscribe__has_permission__ok(self, api_client, mocker):

        # arrange
        user = create_test_user()
        check_permission_mock = mocker.patch(
            'pneumatic_backend.analytics.customerio'
            '.permissions.WebhookAPIPermission.has_permission',
            return_value=True
        )
        handler_mock = mocker.patch(
            'pneumatic_backend.analytics.customerio.services.WebHookService'
            '.handle',
        )
        data = {
            'metric': 'unsubscribed',
            'data': {
                'identifiers': {
                    'id': str(user.id),
                },
            }
        }

        # act
        response = api_client.post(
            '/analytics/customerio/webhooks',
            data=data
        )

        # assert
        assert response.status_code == 200
        check_permission_mock.assert_called_once()
        handler_mock.assert_called_once_with(data)

    def test_unsubscribe__no_permission__disallow(self, api_client, mocker):

        # arrange
        user = create_test_user()
        check_permission_mock = mocker.patch(
            'pneumatic_backend.analytics.customerio'
            '.permissions.WebhookAPIPermission.has_permission',
            return_value=False
        )
        handler_mock = mocker.patch(
            'pneumatic_backend.analytics.customerio.services.WebHookService'
            '.handle',
        )
        data = {
            'metric': 'unsubscribed',
            'data': {
                'identifiers': {
                    'id': str(user.id),
                },
            }
        }

        # act
        response = api_client.post(
            '/analytics/customerio/webhooks',
            data=data
        )

        # assert
        assert response.status_code == 401
        check_permission_mock.assert_called_once()
        handler_mock.assert_not_called()

    def test_unsupported_metric__ok(self, api_client, mocker):

        # arrange
        check_permission_mock = mocker.patch(
            'pneumatic_backend.analytics.customerio'
            '.permissions.WebhookAPIPermission.has_permission',
            return_value=True
        )
        handler_mock = mocker.patch(
            'pneumatic_backend.analytics.customerio.services.WebHookService'
            '.handle',
        )
        data = {
            'metric': 'undefined',
            'data': {
                'identifiers': {
                    'id': '123',
                },
            }
        }

        # act
        response = api_client.post(
            '/analytics/customerio/webhooks',
            data=data
        )

        # assert
        assert response.status_code == 200
        assert response.data == {}
        check_permission_mock.assert_called_once()
        handler_mock.assert_called_once_with(data)

    def test_user_not_found__ok(self, api_client, mocker):

        # arrange
        check_permission_mock = mocker.patch(
            'pneumatic_backend.analytics.customerio'
            '.permissions.WebhookAPIPermission.has_permission',
            return_value=True
        )
        handler_mock = mocker.patch(
            'pneumatic_backend.analytics.customerio.services.WebHookService'
            '.handle',
            side_effect=WebhookUserNotFound({})
        )
        data = {
            'metric': MetricType.UNSUBSCRIBED,
            'data': {
                'identifiers': {
                    'id': '123',
                },
            }
        }

        # act
        response = api_client.post(
            '/analytics/customerio/webhooks',
            data=data
        )

        # assert
        assert response.status_code == 200
        assert response.data == {}
        check_permission_mock.assert_called_once()
        handler_mock.assert_called_once_with(data)

    def test_unsubscribe__service_exception__validation_error(
        self,
        api_client,
        mocker
    ):

        # arrange
        data = {
            'metric': 'unsubscribed',
            'data': {
                'identifiers': {
                    'id': '1'
                },
            }
        }
        check_permission_mock = mocker.patch(
            'pneumatic_backend.analytics.customerio'
            '.permissions.WebhookAPIPermission.has_permission',
            return_value=True
        )
        handler_mock = mocker.patch(
            'pneumatic_backend.analytics.customerio.services.WebHookService'
            '.handle',
            side_effect=WebhookInvalidData(data=data, details='error')
        )

        # act
        response = api_client.post(
            '/analytics/customerio/webhooks',
            data=data
        )

        # assert
        assert response.status_code == 400
        assert response.data is None
        check_permission_mock.assert_called_once()
        handler_mock.assert_called_once_with(data)
