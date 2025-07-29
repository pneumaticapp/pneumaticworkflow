from django.contrib.auth import get_user_model
from rest_framework.generics import ListAPIView
from pneumatic_backend.accounts.permissions import (
    UserIsAdminOrAccountOwner,
    ExpiredSubscriptionPermission,
    BillingPlanPermission,
)
from pneumatic_backend.processes.models import WorkflowEvent
from pneumatic_backend.reports.serializers import (
    EventHighlightsSerializer,
    HighlightsFilterSerializer
)
from pneumatic_backend.generics.mixins.views import BasePrefetchMixin
from pneumatic_backend.generics.permissions import (
    UserIsAuthenticated,
)


UserModel = get_user_model()


class HighlightsView(
    ListAPIView,
    BasePrefetchMixin,
):
    serializer_class = EventHighlightsSerializer
    permission_classes = (
        UserIsAuthenticated,
        ExpiredSubscriptionPermission,
        BillingPlanPermission,
        UserIsAdminOrAccountOwner,
    )

    def get_queryset(self):
        filter_serializer = HighlightsFilterSerializer(
            data=self.request.query_params
        )
        filter_serializer.is_valid(raise_exception=True)
        queryset = WorkflowEvent.objects.highlights(
            account_id=self.request.user.account.id,
            user_id=self.request.user.id,
            **filter_serializer.validated_data
        )
        queryset = self.prefetch_queryset(queryset)
        return queryset
