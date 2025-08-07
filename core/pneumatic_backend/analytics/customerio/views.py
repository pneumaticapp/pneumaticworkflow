from pneumatic_backend.analytics.customerio.permissions import (
    WebhookAPIPermission
)
from rest_framework.views import APIView
from rest_framework.serializers import ValidationError
from pneumatic_backend.analytics.customerio.services import WebHookService
from pneumatic_backend.analytics.customerio.serializers import (
    WebHookSerializer
)
from pneumatic_backend.analytics.customerio.exceptions import (
    WebHookException,
    UnsupportedMetric,
    WebhookUserNotFound
)
from pneumatic_backend.generics.mixins.views import BaseResponseMixin
from pneumatic_backend.utils import logging


class WebhooksView(
    APIView,
    BaseResponseMixin
):

    permission_classes = (WebhookAPIPermission,)

    def post(self, request, *args, **kwargs):
        slz = WebHookSerializer(data=request.data)
        try:
            slz.is_valid(raise_exception=True)
            WebHookService.handle(slz.validated_data)
        except (UnsupportedMetric, WebhookUserNotFound):
            return self.response_ok(data={})
        except WebHookException as ex:
            logging.capture_sentry_message(
                message='customer.io webhook service error',
                data={'message': ex.message},
                level=logging.SentryLogLevel.ERROR
            )
            return self.response_bad_request()
        except ValidationError as ex:
            logging.capture_sentry_message(
                message='customer.io webhook: validation error',
                data=ex.detail,
                level=logging.SentryLogLevel.ERROR
            )
            return self.response_bad_request()
        else:
            return self.response_ok(data={})
