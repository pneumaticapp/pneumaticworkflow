from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
)
from rest_framework.viewsets import GenericViewSet

from src.accounts.models import APIKey
from src.accounts.permissions import (
    BillingPlanPermission,
    ExpiredSubscriptionPermission,
    UserIsAdminOrAccountOwner,
)
from src.accounts.serializers.api_key import (
    APIKeyCreateSerializer,
    APIKeyListSerializer,
    APIKeyResponseSerializer,
)
from src.accounts.services.api_key import APIKeyService
from src.authentication.permissions import PrivateApiPermission
from src.generics.mixins.views import (
    BaseResponseMixin,
)
from src.generics.permissions import (
    UserIsAuthenticated,
)


class APIKeyViewSet(
    CreateModelMixin,
    ListModelMixin,
    DestroyModelMixin,
    GenericViewSet,
    BaseResponseMixin,
):

    permission_classes = (
        PrivateApiPermission,
        UserIsAuthenticated,
        BillingPlanPermission,
        UserIsAdminOrAccountOwner,
        ExpiredSubscriptionPermission,
    )
    serializer_class = APIKeyListSerializer

    def get_queryset(self):
        return (
            APIKey.objects
            .by_user(self.request.user.id)
            .active()
            .order_by('-date_created')
        )

    def get_serializer_class(self):
        if self.action == 'create':
            return APIKeyCreateSerializer
        return APIKeyListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = APIKeyService(
            user=request.user,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        api_key, raw_key = service.create(
            name=serializer.validated_data.get('name'),
        )

        api_key.key = raw_key
        response_serializer = APIKeyResponseSerializer(api_key)
        return self.response_created(response_serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        service = APIKeyService(
            user=request.user,
            instance=instance,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        service.revoke()
        return self.response_ok()
