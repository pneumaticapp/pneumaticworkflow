from django.contrib.auth import get_user_model
from rest_framework.viewsets import GenericViewSet
from src.generics.mixins.views import (
    CustomViewSetMixin,
)
from src.accounts.serializers.public import (
    PublicAccountSerializer,
)
from src.processes.permissions import PublicTemplatePermission


UserModel = get_user_model()


class PublicAccountViewSet(
    CustomViewSetMixin,
    GenericViewSet,
):

    serializer_class = PublicAccountSerializer
    permission_classes = (PublicTemplatePermission, )

    def get_object(self):
        return self.request.public_template.account

    def get_serializer_context(self, **kwargs):
        context = super().get_serializer_context()
        context['account_owner'] = (
            self.request.public_template.account.get_owner()
        )
        return context

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(instance=self.get_object())
        return self.response_ok(serializer.data)
