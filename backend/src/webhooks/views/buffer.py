from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import GenericViewSet

from src.generics.mixins.views import (
    CustomViewSetMixin,
)
from src.generics.permissions import StagingPermission
from src.openapi.responses import EMPTY, FORBIDDEN, UNAUTHORIZED
from src.openapi.helpers import unpaginated_schema
from src.openapi.internal_serializers import JSON_VALUE_SCHEMA
from src.webhooks.services import (
    WebhookBufferService,
)


class WebHookBufferViewSet(
    CustomViewSetMixin,
    GenericViewSet,
):
    permission_classes = (
        AllowAny,
        StagingPermission,
    )

    @extend_schema(
        tags=['Webhooks'],
        summary='Add a payload to the test webhook buffer',
        description=(
            'Test support operation available only in Development, Testing '
            'or Staging. No session is required. Caches the parsed JSON '
            'payload for inspection; the buffer expires after 600 seconds '
            'without another push. Unavailable in production.'
        ),
        auth=[],
        request={'application/json': JSON_VALUE_SCHEMA},
        responses={204: EMPTY, 401: UNAUTHORIZED, 403: FORBIDDEN},
        examples=[OpenApiExample(
            'Capture a test event',
            value={'event': 'workflow_started', 'workflow_id': 123},
            request_only=True,
        )],
    )
    def create(self, request, *args, **kwargs):
        WebhookBufferService.push(request.data)
        return self.response_ok()

    @unpaginated_schema
    @extend_schema(
        tags=['Webhooks'],
        summary='Read the test webhook buffer',
        description=(
            'Development/Testing/Staging only; no session is required. '
            'Returns a flat array of captured JSON payloads, newest first. '
            'An expired or empty buffer returns []. No pagination.'
        ),
        auth=[],
        responses={200: JSON_VALUE_SCHEMA, 401: UNAUTHORIZED, 403: FORBIDDEN},
    )
    def list(self, *args, **kwargs):
        data = WebhookBufferService.get_list()
        return self.response_ok(data=data)

    @extend_schema(
        tags=['Webhooks'],
        summary='Clear the test webhook buffer',
        description=(
            'Development/Testing/Staging only; no session is required. '
            'Deletes all captured webhook payloads. Unavailable in '
            'production.'
        ),
        auth=[],
        request=None,
        responses={204: EMPTY, 401: UNAUTHORIZED, 403: FORBIDDEN},
    )
    @action(methods=('POST',), detail=False)
    def clear(self, *args, **kwargs):
        WebhookBufferService.clear()
        return self.response_ok()
