from rest_framework.viewsets import GenericViewSet
from pneumatic_backend.accounts.serializers.group import (
    GroupSerializer,
    GroupRequestSerializer,
)
from pneumatic_backend.accounts.permissions import (
    UserIsAdminOrAccountOwner,
)
from pneumatic_backend.generics.permissions import (
    UserIsAuthenticated,
)
from pneumatic_backend.accounts.permissions import (
    SubscriptionPermission,
)
from pneumatic_backend.accounts.models import UserGroup
from pneumatic_backend.generics.mixins.views import (
    CustomViewSetMixin,
)
from pneumatic_backend.utils.validation import raise_validation_error

from pneumatic_backend.accounts.services.group import UserGroupService
from pneumatic_backend.accounts.services.exceptions import (
    UserGroupServiceException
)
from pneumatic_backend.accounts.filters import (
    GroupsListFilterSet,
)
from pneumatic_backend.generics.filters import PneumaticFilterBackend


class GroupViewSet(
    CustomViewSetMixin,
    GenericViewSet
):
    filter_backends = [PneumaticFilterBackend]
    serializer_class = GroupSerializer
    action_filterset_classes = {
        'list': GroupsListFilterSet
    }

    def get_serializer_context(self, **kwargs):
        context = super().get_serializer_context(**kwargs)
        context['account'] = self.request.user.account
        return context

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return (
                UserIsAuthenticated(),
                UserIsAdminOrAccountOwner(),
            )
        else:
            return (
                UserIsAuthenticated(),
                UserIsAdminOrAccountOwner(),
                SubscriptionPermission(),
            )

    def get_queryset(self):
        account_id = self.request.user.account_id
        queryset = UserGroup.objects.on_account(account_id)
        return queryset

    def list(self, request, *args, **kwargs):
        slz = GroupRequestSerializer(data=request.GET)
        slz.is_valid(raise_exception=True)
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return self.response_ok(serializer.data)

    def create(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)
        service = UserGroupService(
            user=request.user,
            is_superuser=request.is_superuser,
            auth_type=request.token_type
        )
        try:
            service.create(**slz.validated_data)
        except UserGroupServiceException as ex:
            raise_validation_error(message=ex.message)
        else:
            return self.response_ok(slz.validated_data)

    def retrieve(self, request, *args, **kwargs):
        group = self.get_object()
        serializer = self.get_serializer(group)
        return self.response_ok(serializer.data)

    def update(self, request, *args, **kwargs):
        group = self.get_object()
        slz = self.get_serializer(group, data=request.data)
        slz.is_valid(raise_exception=True)
        service = UserGroupService(
            user=request.user,
            instance=group,
            is_superuser=request.is_superuser,
            auth_type=request.token_type
        )
        try:
            instance = service.partial_update(
                force_save=True,
                **slz.validated_data
            )
        except UserGroupServiceException as ex:
            raise_validation_error(message=ex.message)
        else:
            serializer = GroupSerializer(instance)
            return self.response_ok(serializer.data)

    def destroy(self, request, *args, **kwargs):
        group = self.get_object()
        group.delete()
        return self.response_ok()
