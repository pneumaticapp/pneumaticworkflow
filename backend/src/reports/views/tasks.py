from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.viewsets import GenericViewSet

from src.accounts.permissions import (
    BillingPlanPermission,
    ExpiredSubscriptionPermission,
)
from src.executor import RawSqlExecutor
from src.generics.mixins.views import CustomViewSetMixin
from src.generics.permissions import (
    UserIsAuthenticated,
)
from src.processes.models.templates.template import Template
from src.reports.queries.tasks import (
    TasksBreakdownByStepsNowQuery,
    TasksBreakdownByStepsQuery,
    TasksBreakdownNowQuery,
    TasksBreakdownQuery,
    TasksOverviewNowQuery,
    TasksOverviewQuery,
)
from src.openapi import (
    ACCESS_AUTH,
    BREAKDOWN_BY_STEPS_PARAMS,
    DATE_RANGE_PARAMS,
    FORBIDDEN,
    UNAUTHORIZED,
)
from src.reports.serializers import (
    BreakdownByStepsFilterSerializer,
    DashboardBreakdownByStepItemSerializer,
    DashboardFilterSerializer,
    DashboardOverviewResponseSerializer,
    TasksDashboardBreakdownItemSerializer,
)


class TasksDashboardViewSet(
    CustomViewSetMixin,
    GenericViewSet,
):
    pagination_class = LimitOffsetPagination
    permission_classes = (
        UserIsAuthenticated,
        ExpiredSubscriptionPermission,
        BillingPlanPermission,
    )

    @extend_schema(
        tags=['Reports'],
        summary='Tasks dashboard overview',
        description=ACCESS_AUTH,
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
            query = TasksOverviewNowQuery(
                account_id=request.user.account_id,
                user_id=request.user.id,
            )
        else:
            query = TasksOverviewQuery(
                account_id=request.user.account_id,
                user_id=request.user.id,
                **filters,
            )
        data = RawSqlExecutor.fetchone(*query.get_sql())
        return self.response_ok(data)

    @extend_schema(
        tags=['Reports'],
        summary='Tasks breakdown',
        description=ACCESS_AUTH,
        parameters=DATE_RANGE_PARAMS,
        responses={
            200: TasksDashboardBreakdownItemSerializer(many=True),
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
            query = TasksBreakdownNowQuery(
                account_id=request.user.account_id,
                user_id=request.user.id,
            )
        else:
            query = TasksBreakdownQuery(
                account_id=request.user.account_id,
                user_id=request.user.id,
                **filters,
            )
        data = list(
            RawSqlExecutor.fetch(*query.get_sql()),
        )
        return self.response_ok(data)

    @extend_schema(
        tags=['Reports'],
        summary='Tasks breakdown by steps',
        description=ACCESS_AUTH,
        parameters=BREAKDOWN_BY_STEPS_PARAMS,
        responses={
            200: DashboardBreakdownByStepItemSerializer(many=True),
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    @action(methods=['get'], detail=False, url_path='by-steps')
    def by_steps(self, request):
        filter_slz = BreakdownByStepsFilterSerializer(data=request.GET)
        filter_slz.is_valid(raise_exception=True)
        filters = filter_slz.validated_data
        get_object_or_404(
            Template.objects.on_account(self.request.user.account_id),
            pk=filters['template_id'],
        )
        if filters.pop('now', None):
            query = TasksBreakdownByStepsNowQuery(
                user_id=request.user.id,
                template_id=filters['template_id'],
            )
        else:
            query = TasksBreakdownByStepsQuery(
                user_id=request.user.id,
                **filters,
            )
        data = list(
            RawSqlExecutor.fetch(*query.get_sql()),
        )
        return self.response_ok(data)
