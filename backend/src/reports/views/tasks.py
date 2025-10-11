from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.viewsets import GenericViewSet
from src.accounts.permissions import (
    ExpiredSubscriptionPermission,
    BillingPlanPermission,
)
from src.executor import RawSqlExecutor
from src.processes.models import Template
from src.reports.queries.tasks import (
    TasksOverviewQuery,
    TasksBreakdownQuery,
    TasksBreakdownByStepsQuery,
    TasksOverviewNowQuery,
    TasksBreakdownNowQuery,
    TasksBreakdownByStepsNowQuery,
)
from src.reports.serializers import (
    BreakdownByStepsFilterSerializer,
    DashboardFilterSerializer,
)
from src.generics.permissions import (
    UserIsAuthenticated,
)
from src.generics.mixins.views import CustomViewSetMixin


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
