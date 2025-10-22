from rest_framework.decorators import action
from rest_framework.mixins import (
    DestroyModelMixin,
    UpdateModelMixin,
)
from rest_framework.viewsets import GenericViewSet

from src.accounts.permissions import (
    BillingPlanPermission,
    ExpiredSubscriptionPermission,
    UserIsAdminOrAccountOwner,
    UsersOverlimitedPermission,
)
from src.generics.mixins.views import CustomViewSetMixin
from src.generics.permissions import (
    UserIsAuthenticated,
)
from src.processes.models.templates.preset import TemplatePreset
from src.processes.permissions import TemplatePresetPermission
from src.processes.serializers.templates.preset import (
    TemplatePresetSerializer,
)
from src.processes.services.exceptions import TemplatePresetServiceException
from src.processes.services.templates.preset import TemplatePresetService
from src.utils.validation import raise_validation_error


class TemplatePresetViewSet(
    CustomViewSetMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    GenericViewSet,
):
    serializer_class = TemplatePresetSerializer
    queryset = TemplatePreset.objects.all()

    def get_permissions(self):
        return (
            UserIsAuthenticated(),
            ExpiredSubscriptionPermission(),
            BillingPlanPermission(),
            UsersOverlimitedPermission(),
            UserIsAdminOrAccountOwner(),
            TemplatePresetPermission(),
        )

    def prefetch_queryset(self, queryset, **kwargs):
        return (
            queryset
            .select_related('author', 'template')
            .prefetch_related('fields')
        )

    def update(self, request, *args, **kwargs):
        preset = self.get_object()
        serializer = self.get_serializer(preset, data=request.data)
        serializer.is_valid(raise_exception=True)

        service = TemplatePresetService(
            user=request.user,
            instance=preset,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        try:
            preset = service.partial_update(
                force_save=True,
                **serializer.validated_data,
            )
        except TemplatePresetServiceException as ex:
            raise_validation_error(message=ex.message)

        return self.response_ok(self.get_serializer(preset).data)

    def destroy(self, request, *args, **kwargs):
        preset = self.get_object()
        service = TemplatePresetService(
            user=request.user,
            instance=preset,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        try:
            service.delete()
        except TemplatePresetServiceException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok()

    @action(methods=['POST'], detail=True, url_path='default')
    def set_default(self, request, *args, **kwargs):
        preset = self.get_object()
        service = TemplatePresetService(
            user=request.user,
            instance=preset,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        try:
            service.set_default()
        except TemplatePresetServiceException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok()
