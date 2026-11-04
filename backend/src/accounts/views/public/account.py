from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework.viewsets import GenericViewSet

from src.accounts.serializers.public.accounts import (
    PublicAccountSerializer,
)
from src.generics.mixins.views import (
    CustomViewSetMixin,
)
from src.openapi.permission_docs import ACCESS_PUBLIC_TEMPLATE
from src.openapi.responses import FORBIDDEN, UNAUTHORIZED
from src.openapi.helpers import unpaginated_schema, with_access_text
from src.openapi.internal_serializers import PublicAccountResponseSerializer
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

    @unpaginated_schema
    @extend_schema(
        tags=['Accounts'],
        summary='Get the public form account settings',
        description=with_access_text(
            'Returns one account object for the public/embedded template '
            'token. Locale settings come from the account owner. Use '
            'X-Public-Authorization: Token <public_or_embed_token>.',
            ACCESS_PUBLIC_TEMPLATE,
        ),
        auth=[{'publicTemplateAuth': []}],
        responses={
            200: PublicAccountResponseSerializer,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(instance=self.get_object())
        return self.response_ok(serializer.data)
