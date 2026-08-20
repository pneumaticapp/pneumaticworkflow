from django.http import Http404
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
    NOT_FOUND,
    UNAUTHORIZED,
    VALIDATION_ERROR,
    WebHookEventSerializer,
    WebHookEventUrlSerializer,
)
from src.webhooks import exceptions
from src.webhooks.serializers import (
    WebHookSubscribeSerializer,
)
from src.webhooks.services import (
    WebhookService,
)


class WebHookEventViewSet(
    CustomViewSetMixin,
    GenericViewSet,
):
    lookup_field = 'event'
    serializer_class = WebHookSubscribeSerializer
    permission_classes = (
        UserIsAuthenticated,
        BillingPlanPermission,
        ExpiredSubscriptionPermission,
        UserIsAdminOrAccountOwner,
    )

    @extend_schema(
        tags=['Webhooks'],
        summary='List webhook events',
        description=ACCESS_ADMIN_BASE,
        responses={
            200: WebHookEventSerializer(many=True),
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    def list(self, request, *args, **kwargs):
        service = WebhookService(
            user=request.user,
            is_superuser=request.is_superuser,
        )
        data = service.get_events()
        return self.response_ok(data)

    @extend_schema(
        tags=['Webhooks'],
        summary='Get webhook event URL',
        description=ACCESS_ADMIN_BASE,
        responses={
            200: WebHookEventUrlSerializer,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    def retrieve(self, request, event, *args, **kwargs):
        try:
            service = WebhookService(
                user=request.user,
                is_superuser=request.is_superuser,
            )
            url = service.get_event_url(event=event)
        except exceptions.InvalidEventException as ex:
            raise Http404 from ex
        return self.response_ok({'url': url})

    @extend_schema(
        tags=['Webhooks'],
        summary='Subscribe to webhook event',
        description=ACCESS_ADMIN_BASE,
        request=WebHookSubscribeSerializer,
        responses={
            200: EMPTY,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    @action(methods=('POST',), detail=True)
    def subscribe(self, request, event, *args, **kwargs):
        slz = WebHookSubscribeSerializer(data=request.data)
        slz.is_valid(raise_exception=True)
        try:
            service = WebhookService(
                user=request.user,
                is_superuser=request.is_superuser,
            )
            service.subscribe_event(
                event=event,
                **slz.validated_data,
            )
        except exceptions.InvalidEventException as ex:
            raise Http404 from ex
        return self.response_ok()

    @extend_schema(
        tags=['Webhooks'],
        summary='Unsubscribe from webhook event',
        description=ACCESS_ADMIN_BASE,
        responses={
            200: EMPTY,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    @action(methods=('POST',), detail=True)
    def unsubscribe(self, request, event, *args, **kwargs):
        try:
            service = WebhookService(
                user=request.user,
                is_superuser=request.is_superuser,
            )
            service.unsubscribe_event(event=event)
        except exceptions.InvalidEventException as ex:
            raise Http404 from ex
        return self.response_ok()
