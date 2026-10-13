from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet

from src.accounts.permissions import (
    BillingPlanPermission,
    ExpiredSubscriptionPermission,
    UserIsAdminOrAccountOwner,
)
from src.generics.mixins.views import (
    CustomViewSetMixin,
)
from src.generics.permissions import (
    UserIsAuthenticated,
)
from src.openapi import (
    ACCESS_ADMIN_BASE,
    EMPTY,
    FORBIDDEN,
    UNAUTHORIZED,
    VALIDATION_ERROR,
)
from src.openapi.examples import WEBHOOK_SUBSCRIBE_EXAMPLE
from src.webhooks.serializers import (
    WebHookSubscribeSerializer,
)
from src.webhooks.services import (
    WebhookService,
)


class WebHookViewSet(
    CustomViewSetMixin,
    GenericViewSet,
):
    serializer_class = WebHookSubscribeSerializer
    permission_classes = (
        UserIsAuthenticated,
        BillingPlanPermission,
        ExpiredSubscriptionPermission,
        UserIsAdminOrAccountOwner,
    )

    @extend_schema(
        tags=['Webhooks'],
        summary='Subscribe to all webhook events',
        description=ACCESS_ADMIN_BASE,
        request=WebHookSubscribeSerializer,
        examples=[WEBHOOK_SUBSCRIBE_EXAMPLE],
        responses={
            200: EMPTY,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    @action(methods=('POST',), detail=False)
    def subscribe(self, request, *args, **kwargs):
        slz = WebHookSubscribeSerializer(data=request.data)
        slz.is_valid(raise_exception=True)
        service = WebhookService(
            user=request.user,
            is_superuser=request.is_superuser,
        )
        service.subscribe(**slz.validated_data)
        return self.response_ok()

    @extend_schema(
        tags=['Webhooks'],
        summary='Unsubscribe from all webhook events',
        description=ACCESS_ADMIN_BASE,
        responses={
            200: EMPTY,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    @action(methods=('POST',), detail=False)
    def unsubscribe(self, request, *args, **kwargs):
        service = WebhookService(
            user=request.user,
            is_superuser=request.is_superuser,
        )
        service.unsubscribe()
        return self.response_ok()
