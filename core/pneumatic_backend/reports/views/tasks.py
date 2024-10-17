from django.conf import settings
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.viewsets import GenericViewSet
from pneumatic_backend.accounts.permissions import (
    ExpiredSubscriptionPermission,
)
from pneumatic_backend.executor import RawSqlExecutor
from pneumatic_backend.processes.models import Template
from pneumatic_backend.reports.queries.tasks import (
    TasksOverviewQuery,
    TasksBreakdownQuery,
    TasksBreakdownByStepsQuery,
    TasksOverviewNowQuery,
    TasksBreakdownNowQuery,
    TasksBreakdownByStepsNowQuery,
)
from pneumatic_backend.reports.serializers import (
    BreakdownByStepsFilterSerializer,
    DashboardFilterSerializer,
)
from pneumatic_backend.generics.permissions import (
    UserIsAuthenticated,
    PaymentCardPermission,
)
from pneumatic_backend.generics.mixins.views import CustomViewSetMixin


class TasksDashboardViewSet(
    CustomViewSetMixin,
    GenericViewSet
):
    pagination_class = LimitOffsetPagination
    permission_classes = (
        UserIsAuthenticated,
        PaymentCardPermission,
        ExpiredSubscriptionPermission
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
                **filters
            )
        data = RawSqlExecutor.fetchone(*query.get_sql(), db=settings.REPLICA)
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
                **filters
            )
        data = list(
            RawSqlExecutor.fetch(
                *query.get_sql(),
                db=settings.REPLICA
            )
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
                **filters
            )
        data = list(
            RawSqlExecutor.fetch(
                *query.get_sql(),
                db=settings.REPLICA
            )
        )
        return self.response_ok(data)
