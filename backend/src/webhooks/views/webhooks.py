from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet
from src.generics.mixins.views import (
    CustomViewSetMixin,
)
from src.accounts.permissions import (
    UserIsAdminOrAccountOwner,
    BillingPlanPermission,
    ExpiredSubscriptionPermission
)
from src.webhooks.services import (
    WebhookService,
)
from src.webhooks.serializers import (
    WebHookSubscribeSerializer,
)
from src.generics.permissions import (
    UserIsAuthenticated,
)


class WebHookViewSet(
    CustomViewSetMixin,
    GenericViewSet
):
    permission_classes = (
        UserIsAuthenticated,
        BillingPlanPermission,
        ExpiredSubscriptionPermission,
        UserIsAdminOrAccountOwner,
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
