from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.viewsets import GenericViewSet
from pneumatic_backend.accounts.permissions import (
    UserIsAdminOrAccountOwner,
    ExpiredSubscriptionPermission,
)
from pneumatic_backend.executor import RawSqlExecutor
from pneumatic_backend.processes.models import Template
from pneumatic_backend.reports.queries.workflows import (
    OverviewQuery,
    WorkflowBreakdownQuery,
    OverviewNowQuery,
    WorkflowBreakdownNowQuery,
    WorkflowBreakdownByTasksQuery,
    WorkflowBreakdownByTasksNowQuery,
)
from pneumatic_backend.reports.serializers import (
    AccountDashboardOverviewSerializer,
    BreakdownByStepsFilterSerializer,
    DashboardFilterSerializer,
)
from pneumatic_backend.generics.mixins.views import CustomViewSetMixin
from pneumatic_backend.generics.permissions import (
    UserIsAuthenticated,
    PaymentCardPermission,
)


class WorkflowsDashboardViewSet(
    CustomViewSetMixin,
    GenericViewSet
):
    pagination_class = LimitOffsetPagination
    permission_classes = (
        UserIsAuthenticated,
        UserIsAdminOrAccountOwner,
        PaymentCardPermission,
        ExpiredSubscriptionPermission
    )
    action_serializer_classes = {
        'overview': AccountDashboardOverviewSerializer,
    }

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
                **filters
            )
        data = RawSqlExecutor.fetchone(*query.get_sql())
        return self.response_ok(data)

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
                **filters
            )
        data = list(RawSqlExecutor.fetch(*query.get_sql()))
        return self.response_ok(data)

    @action(methods=['get'], detail=False, url_path='by-tasks')
    def by_tasks(self, request):
        filter_slz = BreakdownByStepsFilterSerializer(data=request.GET)
        filter_slz.is_valid(raise_exception=True)
        filters = filter_slz.validated_data
        get_object_or_404(
            Template.objects
            .on_account(self.request.user.account_id)
            .with_template_owners(self.request.user.id),
            pk=filters['template_id'],
        )
        if filters.pop('now', None):
            query = WorkflowBreakdownByTasksNowQuery(
                template_id=filters['template_id'],
            )
        else:
            query = WorkflowBreakdownByTasksQuery(
                **filters
            )
        data = list(RawSqlExecutor.fetch(*query.get_sql()))
        return self.response_ok(data)
