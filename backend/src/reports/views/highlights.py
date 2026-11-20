from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListAPIView

from src.accounts.permissions import (
    BillingPlanPermission,
    ExpiredSubscriptionPermission,
)
from src.processes.permissions import UserCanAccessHighlightsPermission
from src.generics.mixins.views import BasePrefetchMixin
from src.generics.permissions import (
    UserIsAuthenticated,
)
from src.openapi.permission_docs import ACCESS_HIGHLIGHTS
from src.openapi.responses import FORBIDDEN, UNAUTHORIZED, VALIDATION_ERROR
from src.openapi.parameters import HIGHLIGHTS_PARAMS
from src.processes.models.workflows.event import WorkflowEvent
from src.reports.serializers import (
    EventHighlightsSerializer,
    HighlightsFilterSerializer,
)

UserModel = get_user_model()


@extend_schema(
    tags=['Reports'],
    summary='Workflow highlights',
    description=ACCESS_HIGHLIGHTS,
    parameters=HIGHLIGHTS_PARAMS,
    responses={
        200: EventHighlightsSerializer(many=True),
        400: VALIDATION_ERROR,
        401: UNAUTHORIZED,
        403: FORBIDDEN,
    },
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
        UserCanAccessHighlightsPermission,
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
        return self.prefetch_queryset(queryset)
