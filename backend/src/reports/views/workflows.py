from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.viewsets import GenericViewSet

from src.accounts.permissions import (
    BillingPlanPermission,
    ExpiredSubscriptionPermission,
)
from src.processes.enums import (
    OwnerType,
    OwnerRole,
)
from src.processes.permissions import (
    UserCanAccessDashboardPermission,
)
from src.executor import RawSqlExecutor
from src.generics.mixins.views import CustomViewSetMixin
from src.generics.permissions import (
    UserIsAuthenticated,
)
from src.processes.models.templates.template import Template
from src.reports.queries.workflows import (
    OverviewNowQuery,
    OverviewQuery,
    WorkflowBreakdownByTasksNowQuery,
    WorkflowBreakdownByTasksQuery,
    WorkflowBreakdownNowQuery,
    WorkflowBreakdownQuery,
)
from src.openapi import (
    ACCESS_DASHBOARD,
    BREAKDOWN_BY_STEPS_PARAMS,
    DATE_RANGE_PARAMS,
    FORBIDDEN,
    UNAUTHORIZED,
)
from src.reports.serializers import (
    AccountDashboardOverviewSerializer,
    BreakdownByStepsFilterSerializer,
    DashboardBreakdownByStepItemSerializer,
    DashboardFilterSerializer,
    DashboardOverviewResponseSerializer,
    WorkflowsDashboardBreakdownItemSerializer,
)


class WorkflowsDashboardViewSet(
    CustomViewSetMixin,
    GenericViewSet,
):
    pagination_class = LimitOffsetPagination
    permission_classes = (
        UserIsAuthenticated,
        ExpiredSubscriptionPermission,
        BillingPlanPermission,
        UserCanAccessDashboardPermission,
    )
    action_serializer_classes = {
        'overview': AccountDashboardOverviewSerializer,
    }

    @extend_schema(
        tags=['Reports'],
        summary='Workflows dashboard overview',
        description=ACCESS_DASHBOARD,
        parameters=DATE_RANGE_PARAMS,
        responses={
            200: DashboardOverviewResponseSerializer,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    @action(methods=['get'], detail=False)
    def overview(self, request):
        filter_slz = DashboardFilterSerializer(data=request.GET)
        filter_slz.is_valid(raise_exception=True)
        filters = filter_slz.validated_data
        if filters.pop('now', None):
            query = OverviewNowQuery(
                account_id=request.user.account_id,
                user_id=request.user.id,
            )
        else:
            query = OverviewQuery(
                account_id=request.user.account_id,
                user_id=request.user.id,
                **filters,
            )
        data = RawSqlExecutor.fetchone(*query.get_sql())
        return self.response_ok(data)

    @extend_schema(
        tags=['Reports'],
        summary='Workflows breakdown',
        description=ACCESS_DASHBOARD,
        parameters=DATE_RANGE_PARAMS,
        responses={
            200: WorkflowsDashboardBreakdownItemSerializer(many=True),
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    @action(methods=['get'], detail=False)
    def breakdown(self, request):
        filter_slz = DashboardFilterSerializer(data=request.GET)
        filter_slz.is_valid(raise_exception=True)
        filters = filter_slz.validated_data
        if filters.pop('now', None):
            query = WorkflowBreakdownNowQuery(
                account_id=request.user.account_id,
                user_id=request.user.id,
            )
        else:
            query = WorkflowBreakdownQuery(
                account_id=request.user.account_id,
                user_id=request.user.id,
                **filters,
            )
        data = list(RawSqlExecutor.fetch(*query.get_sql()))
        return self.response_ok(data)

    @extend_schema(
        tags=['Reports'],
        summary='Workflows breakdown by tasks',
        description=ACCESS_DASHBOARD,
        parameters=BREAKDOWN_BY_STEPS_PARAMS,
        responses={
            200: DashboardBreakdownByStepItemSerializer(many=True),
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    @action(methods=['get'], detail=False, url_path='by-tasks')
    def by_tasks(self, request):
        filter_slz = BreakdownByStepsFilterSerializer(data=request.GET)
        filter_slz.is_valid(raise_exception=True)
        filters = filter_slz.validated_data
        # Check if user has access to template (owner or viewer)
        template_qst = (
            Template.objects
            .on_account(self.request.user.account_id)
            .filter(
                Q(
                    owners__type=OwnerType.USER,
                    owners__user_id=self.request.user.id,
                    owners__is_deleted=False,
                    owners__role__in=(OwnerRole.OWNER, OwnerRole.VIEWER),
                )
                | Q(
                    owners__type=OwnerType.GROUP,
                    owners__group__users__id=self.request.user.id,
                    owners__is_deleted=False,
                    owners__role__in=(OwnerRole.OWNER, OwnerRole.VIEWER),
                ),
            ).distinct()
        )
        get_object_or_404(template_qst, pk=filters['template_id'])
        if filters.pop('now', None):
            query = WorkflowBreakdownByTasksNowQuery(
                template_id=filters['template_id'],
            )
        else:
            query = WorkflowBreakdownByTasksQuery(
                **filters,
            )
        data = list(RawSqlExecutor.fetch(*query.get_sql()))
        return self.response_ok(data)
