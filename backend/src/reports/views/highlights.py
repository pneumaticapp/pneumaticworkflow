from django.contrib.auth import get_user_model
from rest_framework.generics import ListAPIView
from src.accounts.permissions import (
    UserIsAdminOrAccountOwner,
    ExpiredSubscriptionPermission,
    BillingPlanPermission,
)
from src.processes.models import WorkflowEvent
from src.reports.serializers import (
    EventHighlightsSerializer,
    HighlightsFilterSerializer,
)
from src.generics.mixins.views import BasePrefetchMixin
from src.generics.permissions import (
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
            data=self.request.query_params,
        )
        filter_serializer.is_valid(raise_exception=True)
        queryset = WorkflowEvent.objects.highlights(
            account_id=self.request.user.account.id,
            user_id=self.request.user.id,
            **filter_serializer.validated_data,
        )
        queryset = self.prefetch_queryset(queryset)
        return queryset
