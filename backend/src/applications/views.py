from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.pagination import LimitOffsetPagination

from src.accounts.permissions import (
    BillingPlanPermission,
    UserIsAdminOrAccountOwner,
)
from src.applications.models import Integration
from src.applications.serializers import (
    IntegrationSerializer,
    IntegrationsListSerializer,
)
from src.generics.permissions import (
    UserIsAuthenticated,
)
from src.openapi.permission_docs import ACCESS_ADMIN_BASIC
from src.openapi.responses import FORBIDDEN, NOT_FOUND, UNAUTHORIZED
from src.openapi.helpers import LIMIT_OFFSET_LEGACY_NOTE, with_access_text


@extend_schema_view(
    get=extend_schema(
        tags=['Applications'],
        summary='List available integrations',
        description=with_access_text(
            'Lists active integration catalog entries. '
            + LIMIT_OFFSET_LEGACY_NOTE,
            ACCESS_ADMIN_BASIC,
        ),
        responses={
            200: IntegrationsListSerializer(many=True),
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    ),
)
class IntegrationsListView(ListAPIView):
    serializer_class = IntegrationsListSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = (
        UserIsAuthenticated,
        BillingPlanPermission,
        UserIsAdminOrAccountOwner,
    )

    def get_queryset(self):
        return Integration.objects.active()


@extend_schema_view(
    get=extend_schema(
        tags=['Applications'],
        summary='Get integration catalog details',
        description=with_access_text(
            'Returns an active integration entry with its long description '
            'and setup button/link. Inactive or missing entries return 404.',
            ACCESS_ADMIN_BASIC,
        ),
        responses={
            200: IntegrationSerializer,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    ),
)
class IntegrationView(RetrieveAPIView):
    serializer_class = IntegrationSerializer
    permission_classes = (
        UserIsAuthenticated,
        BillingPlanPermission,
        UserIsAdminOrAccountOwner,
    )
    lookup_field = 'pk'
    lookup_url_kwarg = 'pk'

    def get_queryset(self):
        return Integration.objects.active()
