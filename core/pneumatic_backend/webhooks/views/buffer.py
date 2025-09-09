from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import AllowAny

from pneumatic_backend.generics.mixins.views import (
    CustomViewSetMixin,
)
from pneumatic_backend.generics.permissions import StagingPermission
from pneumatic_backend.webhooks.services import (
    WebhookBufferService
)


class WebHookBufferViewSet(
    CustomViewSetMixin,
    GenericViewSet
):
    permission_classes = (
        AllowAny,
        StagingPermission,
    )

    def create(self, request, *args, **kwargs):
        WebhookBufferService.push(request.data)
        return self.response_ok()

    def list(self, *args, **kwargs):
        data = WebhookBufferService.get_list()
        return self.response_ok(data=data)

    @action(methods=('POST',), detail=False)
    def clear(self, *args, **kwargs):
        WebhookBufferService.clear()
        return self.response_ok()
