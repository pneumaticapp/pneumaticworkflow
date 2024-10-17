from abc import abstractmethod
from pneumatic_backend.analytics.messages import (
    MSG_AS_0002,
    MSG_AS_0003,
    MSG_AS_0004,
)
from pneumatic_backend.utils.logging import capture_sentry_message
from pneumatic_backend.analytics.customerio.entities import (
    WebHookData,
)


class WebHookException(Exception):

    @abstractmethod
    def _get_message(self, data: dict, **kwargs):
        pass

    def __init__(self, data: dict, **kwargs):
        self.message = self._get_message(data, **kwargs)
        capture_sentry_message(message=self.message, data=data)
        super().__init__(self.message)


class UnsupportedMetric(WebHookException):

    def _get_message(self, data: WebHookData, **kwargs):
        return MSG_AS_0002(data['metric'])


class WebhookUserNotFound(WebHookException):

    def _get_message(self, *args, **kwargs):
        return MSG_AS_0003


class WebhookInvalidData(WebHookException):

    def _get_message(self, data, **kwargs):
        return MSG_AS_0004(kwargs['details'])
