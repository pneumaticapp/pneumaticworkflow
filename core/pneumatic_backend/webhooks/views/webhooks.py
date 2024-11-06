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
from pneumatic_backend.webhooks.serializers import (
    WebHookSubscribeSerializer,
)
from pneumatic_backend.generics.permissions import (
    UserIsAuthenticated,
)


class WebHookViewSet(
    CustomViewSetMixin,
    GenericViewSet
):
    permission_classes = (
        UserIsAuthenticated,
        UserIsAdminOrAccountOwner,
        ExpiredSubscriptionPermission
    )

    @action(methods=('POST',), detail=False)
    def subscribe(self, request, *args, **kwargs):
        slz = WebHookSubscribeSerializer(data=request.data)
        slz.is_valid(raise_exception=True)
        service = WebhookService(
            user=request.user,
            is_superuser=request.is_superuser
        )
        service.subscribe(**slz.validated_data)
        return self.response_ok()

    @action(methods=('POST',), detail=False)
    def unsubscribe(self, request, *args, **kwargs):
        service = WebhookService(
            user=request.user,
            is_superuser=request.is_superuser
        )
        service.unsubscribe()
        return self.response_ok()
