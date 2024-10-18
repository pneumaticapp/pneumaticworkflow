from rest_framework.decorators import action
from pneumatic_backend.processes.queries import (
    WorkflowCountsByWfStarterQuery,
    WorkflowCountsByCPerformerQuery,
    WorkflowCountsByTemplateTaskQuery,
)
from pneumatic_backend.accounts.permissions import (
    ExpiredSubscriptionPermission,
)

from pneumatic_backend.processes.serializers.workflow_counts import (
    WorkflowCountsResponseSerializer,
    WorkflowCountsByTemplateTaskResponseSerializer,
    WorkflowCountsByWorkflowStarterSerializer,
    WorkflowCountsByCurrentPerformerSerializer,
    WorkflowCountsByTemplateTaskSerializer,
)
from rest_framework.viewsets import GenericViewSet
from pneumatic_backend.generics.mixins.views import CustomViewSetMixin
from pneumatic_backend.executor import RawSqlExecutor
from pneumatic_backend.generics.permissions import UserIsAuthenticated


class WorkflowCountsViewSet(
    CustomViewSetMixin,
    GenericViewSet
):
    permission_classes = (
        UserIsAuthenticated,
        ExpiredSubscriptionPermission,
    )

    def get_serializer_class(self):
        if self.action == 'by_template_task':
            return WorkflowCountsByTemplateTaskResponseSerializer
        else:
            return WorkflowCountsResponseSerializer

    @action(methods=['get'], detail=False, url_path='by-workflow-starter')
    def by_workflow_starter(self, request, *args, **kwargs):
        request_slz = WorkflowCountsByWorkflowStarterSerializer(
            data=request.GET
        )
        request_slz.is_valid(raise_exception=True)
        query = WorkflowCountsByWfStarterQuery(
            user_id=request.user.id,
            account_id=request.user.account_id,
            **request_slz.validated_data
        )
        sql_rows = list(RawSqlExecutor.fetch(*query.get_sql()))
        response_slz = self.get_serializer(instance=sql_rows, many=True)
        return self.response_ok(response_slz.data)

    @action(methods=['get'], detail=False, url_path='by-current-performer')
    def by_current_performer(self, request, *args, **kwargs):
        request_slz = WorkflowCountsByCurrentPerformerSerializer(
            data=request.GET
        )
        request_slz.is_valid(raise_exception=True)
        query = WorkflowCountsByCPerformerQuery(
            user_id=request.user.id,
            account_id=request.user.account_id,
            **request_slz.validated_data
        )
        sql_rows = list(RawSqlExecutor.fetch(*query.get_sql()))
        response_slz = self.get_serializer(instance=sql_rows, many=True)
        return self.response_ok(response_slz.data)

    @action(methods=['get'], detail=False, url_path='by-template-task')
    def by_template_task(self, request, *args, **kwargs):
        request_slz = WorkflowCountsByTemplateTaskSerializer(
            data=request.GET
        )
        request_slz.is_valid(raise_exception=True)
        query = WorkflowCountsByTemplateTaskQuery(
            user_id=request.user.id,
            account_id=request.user.account_id,
            **request_slz.validated_data
        )
        sql_rows = list(RawSqlExecutor.fetch(*query.get_sql()))
        response_slz = self.get_serializer(instance=sql_rows, many=True)
        return self.response_ok(response_slz.data)
