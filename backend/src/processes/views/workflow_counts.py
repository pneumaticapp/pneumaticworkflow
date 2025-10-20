from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet

from src.accounts.permissions import (
    BillingPlanPermission,
    ExpiredSubscriptionPermission,
)
from src.executor import RawSqlExecutor
from src.generics.mixins.views import CustomViewSetMixin
from src.generics.permissions import UserIsAuthenticated
from src.processes.queries import (
    WorkflowCountsByCPerformerQuery,
    WorkflowCountsByTemplateTaskQuery,
    WorkflowCountsByWfStarterQuery,
)
from src.processes.serializers.workflows.workflow_counts import (
    WorkflowCountsByCurrentPerformerSerializer,
    WorkflowCountsByTemplateTaskResponseSerializer,
    WorkflowCountsByTemplateTaskSerializer,
    WorkflowCountsByWorkflowStarterSerializer,
    WorkflowCountsResponseSerializer,
)


class WorkflowCountsViewSet(
    CustomViewSetMixin,
    GenericViewSet,
):
    permission_classes = (
        UserIsAuthenticated,
        BillingPlanPermission,
        ExpiredSubscriptionPermission,
    )

    def get_serializer_class(self):
        if self.action == 'by_template_task':
            return WorkflowCountsByTemplateTaskResponseSerializer
        return WorkflowCountsResponseSerializer

    @action(methods=['get'], detail=False, url_path='by-workflow-starter')
    def by_workflow_starter(self, request, *args, **kwargs):
        request_slz = WorkflowCountsByWorkflowStarterSerializer(
            data=request.GET,
        )
        request_slz.is_valid(raise_exception=True)
        query = WorkflowCountsByWfStarterQuery(
            user_id=request.user.id,
            account_id=request.user.account_id,
            **request_slz.validated_data,
        )
        sql_rows = list(RawSqlExecutor.fetch(*query.get_sql()))
        response_slz = self.get_serializer(instance=sql_rows, many=True)
        return self.response_ok(response_slz.data)

    @action(methods=['get'], detail=False, url_path='by-current-performer')
    def by_current_performer(self, request, *args, **kwargs):
        request_slz = WorkflowCountsByCurrentPerformerSerializer(
            data=request.GET,
        )
        request_slz.is_valid(raise_exception=True)
        query = WorkflowCountsByCPerformerQuery(
            user_id=request.user.id,
            account_id=request.user.account_id,
            **request_slz.validated_data,
        )
        sql_rows = list(RawSqlExecutor.fetch(*query.get_sql()))
        response_slz = self.get_serializer(instance=sql_rows, many=True)
        return self.response_ok(response_slz.data)

    @action(methods=['get'], detail=False, url_path='by-template-task')
    def by_template_task(self, request, *args, **kwargs):
        request_slz = WorkflowCountsByTemplateTaskSerializer(
            data=request.GET,
        )
        request_slz.is_valid(raise_exception=True)
        query = WorkflowCountsByTemplateTaskQuery(
            user_id=request.user.id,
            account_id=request.user.account_id,
            **request_slz.validated_data,
        )
        sql_rows = list(RawSqlExecutor.fetch(*query.get_sql()))
        response_slz = self.get_serializer(instance=sql_rows, many=True)
        return self.response_ok(response_slz.data)
