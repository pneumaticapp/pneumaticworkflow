from django.contrib.auth import get_user_model
from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import GenericViewSet
from src.generics.mixins.views import (
    CustomViewSetMixin,
)
from src.accounts.serializers.public.users import PublicUserSerializer
from src.processes.permissions import PublicTemplatePermission

UserModel = get_user_model()


class PublicUsersViewSet(
    CustomViewSetMixin,
    ListModelMixin,
    GenericViewSet,
):

    permission_classes = (PublicTemplatePermission, )
    serializer_class = PublicUserSerializer

    def get_queryset(self):
        return self.request.public_template.account.users
