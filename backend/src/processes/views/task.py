from typing import List, Optional

from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView, get_object_or_404
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.viewsets import GenericViewSet

from src.accounts.enums import UserType
from src.accounts.permissions import (
    BillingPlanPermission,
    ExpiredSubscriptionPermission,
    UserIsAdminOrAccountOwner,
    UsersOverlimitedPermission,
)
from src.accounts.serializers.user import UserSerializer
from src.analysis.mixins import BaseIdentifyMixin
from src.analysis.services import AnalyticService
from src.generics.filters import PneumaticFilterBackend
from src.generics.mixins.views import (
    CustomViewSetMixin,
)
from src.generics.permissions import (
    IsAuthenticated,
    UserIsAuthenticated,
)
from src.processes.enums import WorkflowEventType
from src.processes.filters import (
    TaskWebhookFilterSet,
    WorkflowEventFilter,
)
from src.processes.models.workflows.event import WorkflowEvent
from src.processes.models.workflows.task import (
    Task,
    TaskForList,
)
from src.processes.permissions import (
    GuestTaskPermission,
    TaskCompletePermission,
    TaskRevertPermission,
    TaskWorkflowMemberPermission,
    TaskWorkflowOwnerPermission,
)
from src.processes.queries import TaskListQuery
from src.processes.serializers.comments import (
    CommentCreateSerializer,
)
from src.processes.serializers.workflows.due_date import (
    DueDateSerializer,
)
from src.processes.serializers.workflows.events import (
    WorkflowEventSerializer,
)
from src.processes.serializers.workflows.task import (
    TaskCompleteSerializer,
    TaskListFilterSerializer,
    TaskListSerializer,
    TaskRevertSerializer,
    TaskSerializer,
)
from src.processes.serializers.workflows.task_performer import (
    TaskGroupPerformerSerializer,
    TaskGuestPerformerSerializer,
    TaskPerformerSerializer,
)
from src.processes.services.events import (
    CommentService,
)
from src.processes.services.exceptions import (
    CommentServiceException,
    WorkflowActionServiceException,
)
from src.processes.services.tasks.exceptions import (
    GroupPerformerServiceException,
    PerformersServiceException,
    TaskFieldException,
    TaskServiceException,
)
from src.processes.services.tasks.groups import (
    GroupPerformerService,
)
from src.processes.services.tasks.guests import (
    GuestPerformersService,
)
from src.processes.services.tasks.performers import (
    TaskPerformersService,
)
from src.processes.services.tasks.task import TaskService
from src.processes.services.workflow_action import (
    WorkflowActionService,
)
from src.processes.throttling import TaskPerformerGuestThrottle
from src.utils.validation import raise_validation_error
from src.webhooks.enums import HookEvent

UserModel = get_user_model()


class TasksListView(ListAPIView):

    serializer_class = TaskListSerializer
    permission_classes = (
        UserIsAuthenticated,
        ExpiredSubscriptionPermission,
        BillingPlanPermission,
    )

    def list(self, request, *args, **kwargs):
        user = request.user
        filter_slz = TaskListFilterSerializer(
            data=request.GET,
            context={'user': user},
        )
        filter_slz.is_valid(raise_exception=True)
        query = TaskListQuery(
            user=user,
            **filter_slz.validated_data,
        )
        self.queryset = TaskForList.objects.execute_raw(query)
        search_text = filter_slz.validated_data.get('search')
        if search_text:
            AnalyticService.search_search(
                user=user,
                page='tasks',
                search_text=search_text,
                is_superuser=request.is_superuser,
                auth_type=request.token_type,
            )
        return super().list(request, *args, **kwargs)


class TaskViewSet(
    CustomViewSetMixin,
    BaseIdentifyMixin,
    GenericViewSet,
):

    filter_backends = (PneumaticFilterBackend,)

    def get_permissions(self):
        if self.action in (
            'retrieve',
            'events',
            'comment',
        ):
            return (
                IsAuthenticated(),
                ExpiredSubscriptionPermission(),
                BillingPlanPermission(),
                TaskWorkflowMemberPermission(),
                GuestTaskPermission(),
            )
        if self.action in (
            'create_performer',
            'delete_performer',
            'create_group_performer',
            'delete_group_performer',
            'create_guest_performer',
            'delete_guest_performer',
            'due_date',
        ):
            return (
                UserIsAuthenticated(),
                ExpiredSubscriptionPermission(),
                BillingPlanPermission(),
                UserIsAdminOrAccountOwner(),
                TaskWorkflowOwnerPermission(),
                UsersOverlimitedPermission(),
            )
        if self.action == 'revert':
            return (
                UserIsAuthenticated(),
                ExpiredSubscriptionPermission(),
                BillingPlanPermission(),
                UsersOverlimitedPermission(),
                TaskRevertPermission(),
            )
        if self.action == 'complete':
            return (
                IsAuthenticated(),
                ExpiredSubscriptionPermission(),
                BillingPlanPermission(),
                UsersOverlimitedPermission(),
                TaskCompletePermission(),
            )
        if self.action == 'webhook_example':
            return (
                UserIsAuthenticated(),
                ExpiredSubscriptionPermission(),
                BillingPlanPermission(),
            )
        return super().get_permissions()

    action_serializer_classes = {
        'retrieve': TaskSerializer,
        'create_performer': TaskPerformerSerializer,
        'delete_performer': TaskPerformerSerializer,
        'create_guest_performer': TaskGuestPerformerSerializer,
        'delete_guest_performer': TaskGuestPerformerSerializer,
        'due_date': DueDateSerializer,
        'create_group_performer': TaskGroupPerformerSerializer,
        'delete_group_performer': TaskGroupPerformerSerializer,
        'events': WorkflowEventSerializer,
        'revert': TaskRevertSerializer,
        'complete': TaskCompleteSerializer,
        'comment': CommentCreateSerializer,
    }

    action_filterset_classes = {
        'events': WorkflowEventFilter,
        'webhook_example': TaskWebhookFilterSet,
    }

    action_paginator_classes = {
        'events': LimitOffsetPagination,
    }

    def get_serializer_context(self, **kwargs):
        context = super().get_serializer_context(**kwargs)
        context['user'] = self.request.user
        context['account'] = self.request.user.account
        return context

    def get_queryset(self):
        user = self.request.user
        queryset = Task.objects.on_account(user.account_id)
        if self.action == 'retrieve':
            queryset = queryset.with_date_first_started()
        elif self.action == 'webhook_example':
            queryset = queryset.filter(
                workflow__owners=user.id,
            ).order_by('-date_started')
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

    def prefetch_queryset(
        self,
        queryset,
        extra_fields: Optional[List[str]] = None,
    ):
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                'checklists__selections',
                'output__selections',
                'output__storage_attachments',
            ).select_related(
                'workflow',
            )
        elif self.action in {'revert', 'complete', 'comment'}:
            queryset = queryset.select_related('workflow')
        return queryset

    @property
    def throttle_classes(self):
        if self.action == 'create_guest_performer':
            return (TaskPerformerGuestThrottle,)
        return ()

    def retrieve(self, request, *args, **kwargs):
        task = self.get_object()
        slz = self.get_serializer(task)
        if request.user.type == UserType.GUEST:
            self.identify(request.user)
            self.group(request.user)
        return self.response_ok(slz.data)

    @action(methods=('POST',), detail=True, url_path='create-performer')
    def create_performer(self, request, *args, **kwargs):
        task = self.get_object()
        request_slz = self.get_serializer(
            data=request.data,
            extra_fields={'task': task},
        )
        request_slz.is_valid(raise_exception=True)
        user_id = request_slz.validated_data['user_id']
        try:
            TaskPerformersService.create_performer(
                task=task,
                request_user=request.user,
                user_key=user_id,
                current_url=request.META.get('HTTP_X_CURRENT_URL'),
                is_superuser=request.is_superuser,
                auth_type=request.token_type,
            )
        except PerformersServiceException as ex:
            raise_validation_error(message=ex.message)
        else:
            return self.response_ok()

    @action(methods=('POST',), detail=True, url_path='create-group-performer')
    def create_group_performer(self, request, *args, **kwargs):
        task = self.get_object()
        request_slz = self.get_serializer(
            data=request.data,
            extra_fields={'task': task},
        )
        request_slz.is_valid(raise_exception=True)
        group_id = request_slz.validated_data['group_id']
        try:
            group_performer_service = GroupPerformerService(
                is_superuser=request.is_superuser,
                auth_type=request.token_type,
                task=task,
                user=request.user,
            )
            group_performer_service.create_performer(group_id=group_id)
        except GroupPerformerServiceException as ex:
            raise_validation_error(message=ex.message)
        else:
            return self.response_ok()

    @action(methods=('POST',), detail=True, url_path='delete-performer')
    def delete_performer(self, request, *args, **kwargs):
        task = self.get_object()
        slz = self.get_serializer(
            data=request.data,
            extra_fields={'task': task},
        )
        slz.is_valid(raise_exception=True)
        user_id = slz.validated_data['user_id']
        try:
            TaskPerformersService.delete_performer(
                task=task,
                request_user=request.user,
                user_key=user_id,
                is_superuser=request.is_superuser,
                auth_type=request.token_type,
            )
        except PerformersServiceException as ex:
            raise_validation_error(message=ex.message)
        else:
            return self.response_ok()

    @action(methods=('POST',), detail=True, url_path='delete-group-performer')
    def delete_group_performer(self, request, *args, **kwargs):
        task = self.get_object()
        request_slz = self.get_serializer(
            data=request.data,
            extra_fields={'task': task},
        )
        request_slz.is_valid(raise_exception=True)
        group_id = request_slz.validated_data['group_id']

        try:
            group_performer_service = GroupPerformerService(
                is_superuser=request.is_superuser,
                auth_type=request.token_type,
                task=task,
                user=request.user,
            )
            group_performer_service.delete_performer(group_id=group_id)
        except GroupPerformerServiceException as ex:
            raise_validation_error(message=ex.message)
        else:
            return self.response_ok()

    @action(methods=('POST',), detail=True, url_path='create-guest-performer')
    def create_guest_performer(self, request, *args, **kwargs):
        task = self.get_object()
        request_slz = self.get_serializer(
            data=request.data,
            extra_fields={'task': task},
        )
        request_slz.is_valid(raise_exception=True)
        email = request_slz.validated_data['email']
        try:
            user, __ = GuestPerformersService.create_performer(
                task=task,
                request_user=request.user,
                user_key=email,
                current_url=request.META.get('HTTP_X_CURRENT_URL'),
                is_superuser=request.is_superuser,
                auth_type=request.token_type,
            )
        except PerformersServiceException as ex:
            raise_validation_error(message=ex.message)
        else:
            response_slz = UserSerializer(instance=user)
            return self.response_ok(response_slz.data)

    @action(methods=('POST',), detail=True, url_path='delete-guest-performer')
    def delete_guest_performer(self, request, *args, **kwargs):
        task = self.get_object()
        request_slz = self.get_serializer(
            data=request.data,
            extra_fields={'task': task},
        )
        request_slz.is_valid(raise_exception=True)
        email = request_slz.validated_data['email']
        try:
            GuestPerformersService.delete_performer(
                task=task,
                request_user=request.user,
                user_key=email,
                is_superuser=request.is_superuser,
                auth_type=request.token_type,
            )
        except PerformersServiceException as ex:
            raise_validation_error(message=ex.message)
        else:
            return self.response_ok()

    @action(methods=('POST', 'DELETE'), detail=True, url_path='due-date')
    def due_date(self, request, *args, **kwargs):
        task = self.get_object()
        if request.method == 'POST':
            request_slz = self.get_serializer(
                data=request.data,
            )
            request_slz.is_valid(raise_exception=True)
            due_date = request_slz.validated_data['due_date_tsp']
        else:
            due_date = None
        service = TaskService(user=request.user, instance=task)
        try:
            service.set_due_date_directly(value=due_date)
        except TaskServiceException as ex:
            raise_validation_error(message=ex.message)
        else:
            return self.response_ok()

    @action(methods=('GET',), detail=True, url_path='events')
    def events(self, request, *args, **kwargs):
        task = self.get_object()
        qst = (
            WorkflowEvent.objects
            .prefetch_related('storage_attachments')
            .on_task(task.id)
            .type_in(WorkflowEventType.TASK_EVENTS)
        )
        qst = self.filter_queryset(qst)
        return self.paginated_response(qst)

    @action(methods=['post'], detail=True)
    def revert(self, request, *args, **kwargs):
        task = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = WorkflowActionService(
            workflow=task.workflow,
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser,
        )
        try:
            service.revert(
                revert_from_task=task,
                comment=serializer.validated_data['comment'],
            )
        except WorkflowActionServiceException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok()

    @action(methods=['post'], detail=True)
    def complete(self, request, *args, **kwargs):
        task = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = WorkflowActionService(
            workflow=task.workflow,
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser,
        )
        try:
            task = service.complete_task_for_user(
                task=task,
                fields_values=serializer.validated_data.get('output'),
            )
            service.check_delay_workflow()
        except WorkflowActionServiceException as ex:
            raise_validation_error(message=ex.message)
        except TaskFieldException as ex:
            raise_validation_error(
                message=ex.message,
                api_name=ex.api_name,
            )
        response_slz = TaskSerializer(
            instance=task,
            context={'user': request.user},
        )
        return self.response_ok(response_slz.data)

    @action(methods=['post'], detail=True)
    def comment(self, request, *args, **kwargs):
        task = self.get_object()
        slz = self.get_serializer(
            data=request.data,
            extra_fields={'workflow': task.workflow},
        )
        slz.is_valid(raise_exception=True)
        service = CommentService(
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser,
        )
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

    @action(methods=['get'], url_path='webhook-example', detail=False)
    def webhook_example(self, request, *args, **kwargs):
        task = self.filter_queryset(self.get_queryset()).first()
        if not task:
            return self.response_not_found()
        return self.response_ok(
            {
                'hook': {
                    "event": (
                        HookEvent.TASK_COMPLETED if task.is_completed
                        else HookEvent.TASK_RETURNED
                    ),
                    'id': 123,
                    "target": 'https://example.com/webhooks/',
                },
                **task.webhook_payload(),
            },
        )
