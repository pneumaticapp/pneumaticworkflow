from rest_framework.serializers import ValidationError
from rest_framework.views import APIView

from src.analysis.customerio.exceptions import (
    UnsupportedMetric,
    WebHookException,
    WebhookUserNotFound,
)
from src.analysis.customerio.permissions import (
    WebhookAPIPermission,
)
from src.analysis.customerio.serializers import (
    WebHookSerializer,
)
from src.analysis.customerio.services import WebHookService
from src.generics.mixins.views import BaseResponseMixin
from src.utils import logging


class WebhooksView(
    APIView,
    BaseResponseMixin,
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
                level=logging.SentryLogLevel.ERROR,
            )
            return self.response_bad_request()
        except ValidationError as ex:
            logging.capture_sentry_message(
                message='customer.io webhook: validation error',
                data=ex.detail,
                level=logging.SentryLogLevel.ERROR,
            )
            return self.response_bad_request()
        else:
            return self.response_ok(data={})
