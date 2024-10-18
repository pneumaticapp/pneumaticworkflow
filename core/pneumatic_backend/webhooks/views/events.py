from django.http import Http404
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet
from pneumatic_backend.generics.mixins.views import (
    CustomViewSetMixin,
)
from pneumatic_backend.accounts.permissions import (
    UserIsAdminOrAccountOwner,
    ExpiredSubscriptionPermission
)
from pneumatic_backend.webhooks.services import (
    WebhookService,
)
from pneumatic_backend.webhooks import exceptions
from pneumatic_backend.webhooks.serializers import (
    WebHookSubscribeSerializer,
)
from pneumatic_backend.generics.permissions import (
    UserIsAuthenticated,
)


class WebHookEventViewSet(
    CustomViewSetMixin,
    GenericViewSet
):
    lookup_field = 'event'
    permission_classes = (
        UserIsAuthenticated,
        UserIsAdminOrAccountOwner,
        ExpiredSubscriptionPermission
    )

    def list(self, request, *args, **kwargs):
        service = WebhookService(
            user=request.user,
            is_superuser=request.is_superuser
        )
        data = service.get_events()
        return self.response_ok(data)

    def retrieve(self, request, event, *args, **kwargs):
        try:
            service = WebhookService(
                user=request.user,
                is_superuser=request.is_superuser
            )
            url = service.get_event_url(event=event)
        except exceptions.InvalidEventException:
            raise Http404
        return self.response_ok({'url': url})

    @action(methods=('POST',), detail=True)
    def subscribe(self, request, event, *args, **kwargs):
        slz = WebHookSubscribeSerializer(data=request.data)
        slz.is_valid(raise_exception=True)
        try:
            service = WebhookService(
                user=request.user,
                is_superuser=request.is_superuser
            )
            service.subscribe_event(
                event=event,
                **slz.validated_data
            )
        except exceptions.InvalidEventException:
            raise Http404
        return self.response_ok()

    @action(methods=('POST',), detail=True)
    def unsubscribe(self, request, event, *args, **kwargs):
        try:
            service = WebhookService(
                user=request.user,
                is_superuser=request.is_superuser
            )
            service.unsubscribe_event(event=event)
        except exceptions.InvalidEventException:
            raise Http404
        return self.response_ok()
