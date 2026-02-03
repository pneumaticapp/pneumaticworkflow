from rest_framework.decorators import action
from rest_framework.generics import (
    get_object_or_404,
)
from rest_framework.mixins import ListModelMixin, UpdateModelMixin
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.viewsets import GenericViewSet

from src.accounts.enums import UserType
from src.accounts.permissions import (
    AccountOwnerPermission,
    BillingPlanPermission,
    ExpiredSubscriptionPermission,
    UserIsAdminOrAccountOwner,
    UsersOverlimitedPermission,
)
from src.analysis.actions import WorkflowActions
from src.analysis.services import AnalyticService
from src.generics.filters import PneumaticFilterBackend
from src.generics.mixins.views import CustomViewSetMixin
from src.generics.paginations import DefaultPagination
from src.generics.permissions import (
    IsAuthenticated,
    UserIsAuthenticated,
)
from src.processes.enums import WorkflowEventType
from src.processes.filters import (
    WorkflowEventFilter,
    WorkflowWebhookFilterSet,
)
from src.processes.models.workflows.event import WorkflowEvent
from src.processes.models.workflows.workflow import Workflow
from src.processes.paginations import WorkflowListPagination
from src.processes.permissions import (
    GuestWorkflowEventsPermission,
    GuestWorkflowPermission,
    WorkflowMemberPermission,
    WorkflowOwnerPermission,
)
from src.processes.serializers.comments import CommentCreateSerializer
from src.processes.serializers.workflows.events import WorkflowEventSerializer
from src.processes.serializers.workflows.workflow import (
    WorkflowDetailsSerializer,
    WorkflowFieldsFilterSerializer,
    WorkflowFieldsSerializer,
    WorkflowFinishSerializer,
    WorkflowListFilterSerializer,
    WorkflowListSerializer,
    WorkflowReturnToTaskSerializer,
    WorkflowSnoozeSerializer,
    WorkflowTaskCompleteSerializer,
    WorkflowUpdateSerializer,
)
from src.processes.services.events import CommentService
from src.processes.services.exceptions import (
    CommentServiceException,
    WorkflowActionServiceException,
)
from src.processes.services.tasks.exceptions import TaskFieldException
from src.processes.services.workflow_action import WorkflowActionService
from src.utils.validation import raise_validation_error
from src.webhooks.enums import HookEvent


class WorkflowViewSet(
    CustomViewSetMixin,
    ListModelMixin,
    UpdateModelMixin,
    GenericViewSet,
):

    filter_backends = (PneumaticFilterBackend, )
    action_serializer_classes = {
        'retrieve': WorkflowDetailsSerializer,
        'comment': CommentCreateSerializer,
        'complete': WorkflowTaskCompleteSerializer,
        'return_to': WorkflowReturnToTaskSerializer,
        'finish': WorkflowFinishSerializer,
        'partial_update': WorkflowUpdateSerializer,
        'list': WorkflowListSerializer,
        'fields': WorkflowFieldsSerializer,
        'snooze': WorkflowDetailsSerializer,
        'events': WorkflowEventSerializer,
        'resume': WorkflowDetailsSerializer,
    }
    action_filterset_classes = {
        'events': WorkflowEventFilter,
        'webhook_example': WorkflowWebhookFilterSet,
    }

    action_paginator_classes = {
        'events': LimitOffsetPagination,
        'fields': DefaultPagination,
        'list': WorkflowListPagination,
    }

    def get_serializer_context(self, **kwargs):
        context = super().get_serializer_context(**kwargs)
        context['user'] = self.request.user
        context['account'] = self.request.user.account
        context['is_superuser'] = self.request.is_superuser
        context['auth_type'] = self.request.token_type
        if self.request.user.is_guest:
            context['guest_task_id'] = self.request.task_id
        return context

    def get_queryset(self):
        user = self.request.user
        queryset = Workflow.objects.on_account(user.account_id)
        if self.action in ('list', 'fields'):
            queryset = queryset.with_member(user)
        elif self.action == 'webhook_example':
            queryset = queryset.filter(
                owners=user.id,
            ).order_by('-date_created')
        return self.prefetch_queryset(queryset)

    def get_object(self):

        """ Don't filter queryset by default """

        queryset = self.get_queryset()
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        assert lookup_url_kwarg in self.kwargs, (
            f'Expected view {self.__class__.__name__} '
            f'to be called with a URL keyword argument '
            f'named "{lookup_url_kwarg}". '
            f'Fix your URL conf, or set the `.lookup_field` '
            f'attribute on the view correctly.'
        )
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = get_object_or_404(queryset, **filter_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj

    def get_permissions(self):
        if self.action == 'list':
            return (
                UserIsAuthenticated(),
                BillingPlanPermission(),
                ExpiredSubscriptionPermission(),
                UserIsAdminOrAccountOwner(),
            )
        if self.action == 'fields':
            return (
                AccountOwnerPermission(),
                BillingPlanPermission(),
                ExpiredSubscriptionPermission(),
            )
        if self.action == 'retrieve':
            return (
                UserIsAuthenticated(),
                BillingPlanPermission(),
                ExpiredSubscriptionPermission(),
                WorkflowMemberPermission(),
            )
        if self.action in (
            'destroy',
            'terminate',
            'resume',
            'snooze',
            'finish',
            'return_to',
        ):
            return (
                UserIsAuthenticated(),
                BillingPlanPermission(),
                ExpiredSubscriptionPermission(),
                UserIsAdminOrAccountOwner(),
                WorkflowOwnerPermission(),
                UsersOverlimitedPermission(),
            )
        if self.action == 'partial_update':
            return (
                UserIsAuthenticated(),
                BillingPlanPermission(),
                ExpiredSubscriptionPermission(),
                WorkflowOwnerPermission(),
                UsersOverlimitedPermission(),
            )
        if self.action == 'comment':
            return (
                IsAuthenticated(),
                BillingPlanPermission(),
                ExpiredSubscriptionPermission(),
                UsersOverlimitedPermission(),
                GuestWorkflowPermission(),
                WorkflowMemberPermission(),
            )
        if self.action == 'complete':
            return (
                IsAuthenticated(),
                BillingPlanPermission(),
                ExpiredSubscriptionPermission(),
                UsersOverlimitedPermission(),
                GuestWorkflowPermission(),
            )
        if self.action == 'events':
            return (
                IsAuthenticated(),
                BillingPlanPermission(),
                ExpiredSubscriptionPermission(),
                GuestWorkflowEventsPermission(),
                WorkflowMemberPermission(),
            )
        if self.action == 'webhook_example':
            return (
                UserIsAuthenticated(),
                ExpiredSubscriptionPermission(),
                BillingPlanPermission(),
            )
        return super().get_permissions()

    def list(self, request, *args, **kwargs):
        filter_slz = WorkflowListFilterSerializer(data=request.GET)
        filter_slz.is_valid(raise_exception=True)
        qst = Workflow.objects.raw_list_query(
            **filter_slz.validated_data,
            account_id=request.user.account_id,
            user_id=request.user.id,
        )
        return self.paginated_response(qst)

    def retrieve(self, request, pk=None):
        queryset = self.get_queryset()
        instance = get_object_or_404(queryset, id=pk)
        serializer = self.get_serializer(instance)
        return self.response_ok(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        workflow = get_object_or_404(queryset, id=kwargs.get('pk'))

        serializer = self.get_serializer(
            instance=workflow,
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        is_urgent = serializer.validated_data.get('is_urgent')
        is_urgent_changed = (
            is_urgent is not None and is_urgent != workflow.is_urgent
        )
        workflow = serializer.save()
        AnalyticService.workflows_updated(
            workflow=workflow,
            auth_type=request.token_type,
            is_superuser=request.is_superuser,
            user=request.user,
        )
        if is_urgent_changed:
            AnalyticService.workflows_urgent(
                workflow=workflow,
                auth_type=request.token_type,
                is_superuser=request.is_superuser,
                user=request.user,
                action=(
                    WorkflowActions.marked if is_urgent else
                    WorkflowActions.unmarked
                ),
            )
        return self.response_ok(
            WorkflowDetailsSerializer(instance=workflow).data,
        )

    @action(methods=['post'], detail=True)
    def comment(self, request, *args, **kwargs):
        workflow = self.get_object()
        slz = self.get_serializer(
            data=request.data,
            extra_fields={'workflow': workflow},
        )
        slz.is_valid(raise_exception=True)
        service = CommentService(
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser,
        )
        task = workflow.tasks.active_or_delayed().order_by('-number').first()
        try:
            event = service.create(
                task=task,
                **slz.validated_data,
            )
        except CommentServiceException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok(
            WorkflowEventSerializer(instance=event).data,
        )

    @action(methods=['post'], detail=True, url_path='task-complete')
    def complete(self, request, *args, **kwargs):
        workflow = self.get_object()
        serializer = self.get_serializer(
            data=request.data,
            extra_fields={'workflow': workflow},
        )
        serializer.is_valid(raise_exception=True)
        service = WorkflowActionService(
            workflow=workflow,
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser,
        )
        try:
            service.complete_task_for_user(
                task=serializer.validated_data['task'],
                fields_values=serializer.validated_data.get('output'),
            )
        except WorkflowActionServiceException as ex:
            raise_validation_error(message=ex.message)
        except TaskFieldException as ex:
            raise_validation_error(
                message=ex.message,
                api_name=ex.api_name,
            )
        return self.response_ok()

    @action(methods=['post'], detail=True, url_path='return-to')
    def return_to(self, request, **kwargs):
        workflow = self.get_object()
        serializer = self.get_serializer(
            data=request.data,
            extra_fields={'workflow': workflow},
        )
        serializer.is_valid(raise_exception=True)
        service = WorkflowActionService(
            workflow=workflow,
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser,
        )
        try:
            service.return_to(
                revert_to_task=serializer.validated_data['task'],
            )
        except WorkflowActionServiceException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok()

    def destroy(self, request, *args, **kwargs):
        service = WorkflowActionService(
            workflow=self.get_object(),
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser,
        )
        try:
            service.terminate_workflow()
        except WorkflowActionServiceException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok()

    @action(methods=['post'], detail=True, url_path='close')
    def terminate(self, request, *args, **kwargs):
        # Deprecated. Will be removed in my.pneumatic.app/workflows/34225/
        service = WorkflowActionService(
            workflow=self.get_object(),
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser,
        )
        try:
            service.terminate_workflow()
        except WorkflowActionServiceException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok()

    @action(methods=['post'], detail=True)
    def resume(self, request, *args, **kwargs):
        workflow = self.get_object()
        service = WorkflowActionService(
            workflow=workflow,
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser,
        )
        try:
            service.force_resume_workflow()
        except WorkflowActionServiceException as ex:
            raise_validation_error(message=ex.message)
        serializer = self.get_serializer(workflow)
        return self.response_ok(serializer.data)

    @action(methods=['post'], detail=True)
    def finish(self, request, *args, **kwargs):
        workflow = self.get_object()
        serializer = self.get_serializer(
            instance=workflow,
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        service = WorkflowActionService(
            workflow=workflow,
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser,
        )
        service.force_complete_workflow()
        AnalyticService.workflows_ended(
            user=request.user,
            workflow=workflow,
            auth_type=request.token_type,
            is_superuser=request.is_superuser,
        )
        return self.response_ok()

    @action(methods=['get'], detail=False)
    def fields(self, request, *args, **kwargs):
        filter_slz = WorkflowFieldsFilterSerializer(data=request.GET)
        filter_slz.is_valid(raise_exception=True)
        qst = Workflow.objects.fields_query(
            **filter_slz.validated_data,
            account_id=request.user.account_id,
        )
        return self.paginated_response(qst)

    @action(methods=['post'], detail=True)
    def snooze(self, request, *args, **kwargs):
        request_slz = WorkflowSnoozeSerializer(data=request.data)
        request_slz.is_valid(raise_exception=True)
        workflow = self.get_object()
        service = WorkflowActionService(
            workflow=workflow,
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser,
        )
        try:
            service.force_delay_workflow(
                date=request_slz.validated_data['date'],
            )
        except WorkflowActionServiceException as ex:
            raise_validation_error(message=ex.message)
        serializer = self.get_serializer(workflow)
        return self.response_ok(serializer.data)

    @action(methods=['get'], detail=True)
    def events(self, request, *args, **kwargs):
        workflow = self.get_object()
        qst = WorkflowEvent.objects.on_workflow(
            workflow.id,
        ).exclude_type(WorkflowEventType.RUN)
        if self.request.user.type == UserType.GUEST:
            qst = qst.by_task(
                self.request.task_id,
            ).exclude(type=WorkflowEventType.TASK_START)
        qst = self.filter_queryset(qst)
        return self.paginated_response(qst)

    @action(methods=['get'], url_path='webhook-example', detail=False)
    def webhook_example(self, request, *args, **kwargs):
        workflow = self.filter_queryset(self.get_queryset()).first()
        if not workflow:
            return self.response_not_found()
        return self.response_ok(
            {
                'hook': {
                    "event": (
                        HookEvent.WORKFLOW_COMPLETED if workflow.is_completed
                        else HookEvent.WORKFLOW_STARTED
                    ),
                    'id': 123,
                    "target": 'https://example.com/webhooks/',
                },
                **workflow.webhook_payload(),
            },
        )
