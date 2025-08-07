import os
from typing import Optional
from django.contrib.auth import get_user_model
from pneumatic_backend.analytics.customerio.entities import (
    WebHookData,
    WebHookMetricData,
)
from pneumatic_backend.analytics.enums import MailoutType
from pneumatic_backend.analytics.customerio.enums import MetricType
from pneumatic_backend.analytics.customerio import exceptions


configuration = os.getenv('ENVIRONMENT', 'development').title()
UserModel = get_user_model()


class CommonMixin:

    @classmethod
    def _get_webhook_user(
        cls,
        data: WebHookMetricData
    ) -> Optional[UserModel]:

        user_id = data['identifiers']['id']
        user = UserModel.objects.by_id(user_id).first()
        if user is None and configuration == 'Production':
            raise exceptions.WebhookUserNotFound(data)
        return user


class UnsubscribeMixin:

    @classmethod
    def _unsubscribe_handler(cls, data: WebHookMetricData):
        user = cls._get_webhook_user(data)
        if user:
            setattr(user, MailoutType.MAP[MailoutType.NEWSLETTER], False)
            user.save()


class SubscribeMixin:

    @classmethod
    def _subscribe_handler(cls, data: WebHookMetricData):
        user = cls._get_webhook_user(data)
        if user:
            setattr(user, MailoutType.MAP[MailoutType.NEWSLETTER], True)
            user.save()


class WebHookService(
    CommonMixin,
    SubscribeMixin,
    UnsubscribeMixin
):

    @classmethod
    def handle(cls, data: WebHookData):
        try:
            metric = data['metric']
            if metric == MetricType.UNSUBSCRIBED:
                cls._unsubscribe_handler(data['data'])
            elif metric == MetricType.SUBSCRIBED:
                cls._subscribe_handler(data['data'])
            else:
                raise exceptions.UnsupportedMetric(data)
        except KeyError as ex:
            raise exceptions.WebhookInvalidData(data, details=str(ex))
