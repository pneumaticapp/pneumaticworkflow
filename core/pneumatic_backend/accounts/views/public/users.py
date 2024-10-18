from django.contrib.auth import get_user_model
from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import GenericViewSet
from pneumatic_backend.generics.mixins.views import (
    CustomViewSetMixin,
)
from pneumatic_backend.accounts.serializers.public import PublicUserSerializer
from pneumatic_backend.processes.permissions import PublicTemplatePermission

UserModel = get_user_model()


class PublicUsersViewSet(
    CustomViewSetMixin,
    ListModelMixin,
    GenericViewSet,
):

    permission_classes = (PublicTemplatePermission, )
    serializer_class = PublicUserSerializer

    def get_queryset(self):
        queryset = self.request.public_template.account.users
        return queryset
