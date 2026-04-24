from django.contrib.auth import get_user_model
from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import GenericViewSet

from src.accounts.filters import PublicUsersListFilterSet
from src.accounts.serializers.public.users import PublicUserSerializer
from src.generics.filters import PneumaticFilterBackend
from src.generics.mixins.views import (
    CustomViewSetMixin,
)
from src.processes.permissions import PublicTemplatePermission

UserModel = get_user_model()


class PublicUsersViewSet(
    CustomViewSetMixin,
    ListModelMixin,
    GenericViewSet,
):

    permission_classes = (PublicTemplatePermission, )
    filter_backends = [PneumaticFilterBackend]
    serializer_class = PublicUserSerializer
    action_filterset_classes = {
        'list': PublicUsersListFilterSet,
    }

    def get_queryset(self):
        queryset = self.request.public_template.account.users
        return self.prefetch_queryset(queryset)
