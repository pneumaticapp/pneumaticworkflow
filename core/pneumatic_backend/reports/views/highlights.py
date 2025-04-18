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

        templates = filter_serializer.validated_data.get('templates')
        users = filter_serializer.validated_data.get('current_performer_ids')
        date_before_tsp = filter_serializer.validated_data.get(
            'date_before_tsp'
        )
        date_after_tsp = filter_serializer.validated_data.get(
            'date_after_tsp'
        )

        queryset = WorkflowEvent.objects.highlights(
            self.request.user.account.id,
            user_id=self.request.user.id,
            templates=templates,
            users=users,
            date_before_tsp=date_before_tsp,
            date_after_tsp=date_after_tsp
        )
        queryset = self.prefetch_queryset(queryset)
        return queryset
