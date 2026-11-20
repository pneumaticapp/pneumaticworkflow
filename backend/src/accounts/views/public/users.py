from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import GenericViewSet

from src.accounts.filters import PublicUsersListFilterSet
from src.accounts.serializers.public.users import PublicUserSerializer
from src.generics.filters import PneumaticFilterBackend
from src.generics.mixins.views import (
    CustomViewSetMixin,
)
from src.openapi.permission_docs import ACCESS_PUBLIC_TEMPLATE
from src.openapi.responses import FORBIDDEN, UNAUTHORIZED
from src.openapi.helpers import LIMIT_OFFSET_LEGACY_NOTE, with_access_text
from src.processes.permissions import PublicTemplatePermission

UserModel = get_user_model()


@extend_schema_view(
    list=extend_schema(
        tags=['Accounts'],
        summary='List public form account users',
        description=with_access_text(
            'Lists users on the account identified by the public/embedded '
            'template token. Use X-Public-Authorization: Token <token>. '
            'Order by first_name, last_name or status; prefix with - to '
            'reverse a field. Default ordering is last_name. '
            + LIMIT_OFFSET_LEGACY_NOTE,
            ACCESS_PUBLIC_TEMPLATE,
        ),
        auth=[{'publicTemplateAuth': []}],
        responses={
            200: PublicUserSerializer(many=True),
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    ),
)
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
