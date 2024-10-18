import pytest
from pneumatic_backend.analytics.customerio.services import (
    WebHookService
)
from pneumatic_backend.analytics.tests.fixtures import (
    create_test_user
)
from pneumatic_backend.analytics.customerio.enums import MetricType
from pneumatic_backend.analytics.customerio import exceptions
from pneumatic_backend.analytics import messages


pytestmark = pytest.mark.django_db


class TestWebHookService:

    def test_get_webhook_user__ok(self):
        # arrange
        user = create_test_user()
        data = {
            'identifiers': {
                'id': user.id,
            }
        }

        # act
        result = WebHookService._get_webhook_user(data)

        # assert
        assert result == user

    def test_get_webhook_user__user_not_found_prod_env__raise_exception(
        self,
        mocker
    ):
        # arrange
        data = {
            'identifiers': {
                'id': 999,
            }
        }
        mocker.patch(
            'pneumatic_backend.analytics.customerio.services.configuration',
            'Production'
        )

        # act
        with pytest.raises(exceptions.WebhookUserNotFound) as ex:
            WebHookService._get_webhook_user(data)

        # assert
        assert str(ex.value) == messages.MSG_AS_0003

    def test_get_webhook_user__user_not_found_dev_env__return_none(
        self,
        mocker
    ):
        # arrange
        data = {
            'identifiers': {
                'id': 999,
            }
        }
        mocker.patch(
            'pneumatic_backend.analytics.customerio.services.configuration',
            'Staging'
        )

        # act
        user = WebHookService._get_webhook_user(data)

        # assert
        assert user is None

    def test_handle__subscribe_metric__ok(self, mocker):

        # arrange
        metric_data = {
            'identifiers': {
                'email': 'example@mail.ru',
            }
        }
        webhook_data = {
            'metric': MetricType.SUBSCRIBED,
            'data': metric_data
        }
        subscribe_handler_mock = mocker.patch(
            'pneumatic_backend.analytics.customerio.services'
            '.WebHookService._subscribe_handler'
        )

        # act
        WebHookService.handle(webhook_data)

        # assert
        subscribe_handler_mock.assert_called_once_with(
            metric_data
        )

    def test_handle__unsubscribe_metric__ok(self, mocker):

        # arrange
        metric_data = {
            'identifiers': {
                'email': 'example@mail.ru',
            }
        }
        webhook_data = {
            'metric': MetricType.UNSUBSCRIBED,
            'data': metric_data
        }
        unsubscribe_handler_mock = mocker.patch(
            'pneumatic_backend.analytics.customerio.services'
            '.WebHookService._unsubscribe_handler'
        )

        # act
        WebHookService.handle(webhook_data)

        # assert
        unsubscribe_handler_mock.assert_called_once_with(
            metric_data
        )

    def test_handle__unsupported_metric__raise_exception(self, mocker):

        # arrange
        metric = 'undefined'
        webhook_data = {
            'metric': metric,
            'data': {}
        }
        unsubscribe_handler_mock = mocker.patch(
            'pneumatic_backend.analytics.customerio.services'
            '.WebHookService._unsubscribe_handler'
        )

        # act
        with pytest.raises(exceptions.UnsupportedMetric) as ex:
            WebHookService.handle(webhook_data)

        # assert
        unsubscribe_handler_mock.assert_not_called()
        assert str(ex.value) == messages.MSG_AS_0002(metric)

    def test_handle__invalid_format__raise_exception(
        self,
    ):

        # arrange
        data = {
            'mepric': MetricType.UNSUBSCRIBED,
            'data': {
                'user': {
                    'id': 999,
                }
            }
        }

        # act
        with pytest.raises(exceptions.WebhookInvalidData) as ex:
            WebHookService.handle(data)

        # assert
        assert str(ex.value) == messages.MSG_AS_0004('\'metric\'')

    def test_unsubscribe_handler__ok(self, mocker):

        # arrange
        user = create_test_user()
        data = {
            'identifiers': {
                'id': user.id,
            }
        }
        get_user_mock = mocker.patch(
            'pneumatic_backend.analytics.customerio.services'
            '.WebHookService._get_webhook_user',
            return_value=user
        )

        # act
        WebHookService._unsubscribe_handler(data)

        # assert
        user.refresh_from_db()
        get_user_mock.assert_called_once_with(data)
        assert user.is_newsletters_subscriber is False

    def test_unsubscribe_handler__not_user__skip(self, mocker):

        # arrange
        data = {
            'identifiers': {
                'id': 999,
            }
        }
        get_user_mock = mocker.patch(
            'pneumatic_backend.analytics.customerio.services'
            '.WebHookService._get_webhook_user',
            return_value=None
        )

        # act
        WebHookService._unsubscribe_handler(data)

        # assert
        get_user_mock.assert_called_once_with(data)

    def test_subscribe_handler__not_user__skip(self, mocker):

        # arrange
        data = {
            'identifiers': {
                'id': 999,
            }
        }
        get_user_mock = mocker.patch(
            'pneumatic_backend.analytics.customerio.services'
            '.WebHookService._get_webhook_user',
            return_value=None
        )

        # act
        WebHookService._subscribe_handler(data)

        # assert
        get_user_mock.assert_called_once_with(data)

    def test_subscribe_handler__ok(self, mocker):

        # arrange
        user = create_test_user()
        data = {
            'identifiers': {
                'id': user.id,
            }
        }
        get_user_mock = mocker.patch(
            'pneumatic_backend.analytics.customerio.services'
            '.WebHookService._get_webhook_user',
            return_value=user
        )

        # act
        WebHookService._subscribe_handler(data)

        # assert
        user.refresh_from_db()
        get_user_mock.assert_called_once_with(data)
        assert user.is_newsletters_subscriber is True
