from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
)
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
from src.openapi.responses import EMPTY, FORBIDDEN, UNAUTHORIZED
from src.openapi.internal_serializers import EMPTY_OBJECT_SCHEMA
from src.utils import logging


class WebhooksView(
    APIView,
    BaseResponseMixin,
):

    permission_classes = (WebhookAPIPermission,)

    @extend_schema(
        tags=['Applications'],
        summary='Receive Customer.io subscription events',
        description=(
            'Provider callback authenticated by X-CIO-Signature and '
            'X-CIO-Timestamp, not a Pneumatic token. Signature is the hex '
            'HMAC-SHA256 of <configured-api-version>:<timestamp>: followed '
            'by the exact raw request bytes, using the configured webhook '
            'API key. subscribed/unsubscribed metrics change newsletter '
            'preferences for data.identifiers.id. Unsupported metrics or '
            'unknown users are acknowledged with {}. Invalid structure or '
            'service failures return 400 with an empty body.'
        ),
        auth=[{'customerIOSignature': []}],
        parameters=[OpenApiParameter(
            name='X-CIO-Timestamp',
            location=OpenApiParameter.HEADER,
            type=OpenApiTypes.STR,
            required=True,
            description='Timestamp string used verbatim in the HMAC input.',
        )],
        request=WebHookSerializer,
        responses={
            200: EMPTY_OBJECT_SCHEMA,
            400: EMPTY,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
        examples=[OpenApiExample(
            'Newsletter unsubscribe',
            value={
                'metric': 'unsubscribed',
                'data': {'identifiers': {'id': '123'}},
            },
            request_only=True,
        )],
    )
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
