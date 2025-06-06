from rest_framework.pagination import LimitOffsetPagination
from rest_framework.generics import RetrieveAPIView, ListAPIView
from pneumatic_backend.accounts.permissions import (
    UserIsAdminOrAccountOwner,
    BillingPlanPermission,
)
from pneumatic_backend.applications.models import Integration
from pneumatic_backend.applications.serializers import (
    IntegrationsListSerializer,
    IntegrationSerializer
)
from pneumatic_backend.generics.permissions import (
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
