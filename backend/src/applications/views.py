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
