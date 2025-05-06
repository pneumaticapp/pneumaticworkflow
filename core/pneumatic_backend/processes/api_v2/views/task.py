from typing import List
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet
from rest_framework.generics import ListAPIView, get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import LimitOffsetPagination

from pneumatic_backend.analytics.services import AnalyticService
from pneumatic_backend.generics.filters import PneumaticFilterBackend
from pneumatic_backend.generics.permissions import (
    UserIsAuthenticated,
    IsAuthenticated,
)
from pneumatic_backend.accounts.enums import UserType
from pneumatic_backend.processes.enums import TaskStatus
from pneumatic_backend.processes.permissions import (
    TaskWorkflowMemberPermission,
    TaskWorkflowOwnerPermission,
    GuestTaskPermission,
)
from pneumatic_backend.accounts.permissions import (
    UsersOverlimitedPermission,
    UserIsAdminOrAccountOwner,
    ExpiredSubscriptionPermission,
    BillingPlanPermission,
)
from pneumatic_backend.generics.mixins.views import (
    CustomViewSetMixin,
)
from pneumatic_backend.processes.models import (
    Task,
    TaskForList,
    WorkflowEvent,
)
from pneumatic_backend.processes.api_v2.serializers.workflow.task import (
    TaskSerializer,
    TaskListSerializer,
    TaskListFilterSerializer,
)
from pneumatic_backend.processes.api_v2.serializers.workflow.due_date import (
    DueDateSerializer
)
from pneumatic_backend.processes.api_v2.serializers.\
    workflow.task_performer import (
        TaskPerformerSerializer,
        TaskGuestPerformerSerializer,
        TaskGroupPerformerSerializer
    )
from pneumatic_backend.processes.api_v2.serializers.workflow.events import (
    WorkflowEventSerializer,
)
from pneumatic_backend.processes.api_v2.services.task.exceptions import (
    PerformersServiceException,
    TaskServiceException,
    GroupPerformerServiceException
)
from pneumatic_backend.processes.api_v2.services.task.groups import (
    GroupPerformerService
)
from pneumatic_backend.processes.api_v2.services.task.performers import (
    TaskPerformersService
)
from pneumatic_backend.processes.api_v2.services.task.guests import (
    GuestPerformersService
)
from pneumatic_backend.utils.validation import raise_validation_error
from pneumatic_backend.processes.throttling import TaskPerformerGuestThrottle
from pneumatic_backend.analytics.mixins import BaseIdentifyMixin
from pneumatic_backend.accounts.serializers.user import UserSerializer
from pneumatic_backend.processes.queries import TaskListQuery
from pneumatic_backend.processes.api_v2.services.task.task import TaskService
from pneumatic_backend.processes.filters import (
    RecentTaskFilter,
    WorkflowEventFilter,
)
from pneumatic_backend.processes.enums import WorkflowEventType
from rest_framework.response import Response

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
            context={'user': user}
        )
        filter_slz.is_valid(raise_exception=True)
        query = TaskListQuery(
            user=user,
            **filter_slz.validated_data
        )
        self.queryset = TaskForList.objects.execute_raw(
            query,
            using=settings.REPLICA
        )
        search_text = filter_slz.validated_data.get('search')
        if search_text:
            AnalyticService.search_search(
                user=user,
                page='tasks',
                search_text=search_text,
                is_superuser=request.is_superuser,
                auth_type=request.token_type
            )
        return super().list(request, *args, **kwargs)


class RecentTaskView(ListAPIView):
    """ Used by Zapier triggers for get webhook response example"""

    permission_classes = (
        UserIsAuthenticated,
        BillingPlanPermission,
        ExpiredSubscriptionPermission,
    )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecentTaskFilter

    def list(self, request, *args, **kwargs):
        qst = (
            Task.objects
                .on_account(self.request.user.account_id)
                .filter(status__in={TaskStatus.ACTIVE, TaskStatus.COMPLETED})
                .order_by('-date_started')
        )
        task = self.filter_queryset(qst).first()
        return Response(task.webhook_payload()['task'])


class TaskViewSet(
    CustomViewSetMixin,
    BaseIdentifyMixin,
    GenericViewSet,
):

    filter_backends = (PneumaticFilterBackend,)

    def get_permissions(self):
        if self.action in ('retrieve', 'events'):
            return (
                IsAuthenticated(),
                ExpiredSubscriptionPermission(),
                BillingPlanPermission(),
                TaskWorkflowMemberPermission(),
                GuestTaskPermission(),
            )
        elif self.action in (
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
    }

    action_filterset_classes = {
        'events': WorkflowEventFilter,
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
        qst = Task.objects.on_account(user.account_id)
        if self.action == 'retrieve':
            qst = qst.with_date_first_started()
        return self.prefetch_queryset(qst)

    def get_object(self):

        """ Don't filter queryset by default """

        queryset = self.get_queryset()
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = get_object_or_404(queryset, **filter_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj

    def prefetch_queryset(self, queryset, extra_fields: List[str] = None):
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                'checklists__selections',
                'output__selections',
                'output__attachments',
            ).select_related(
                'workflow'
            )
        return queryset

    @property
    def throttle_classes(self):
        if self.action == 'create_guest_performer':
            return (TaskPerformerGuestThrottle,)
        else:
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
            extra_fields={'task': task}
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
                auth_type=request.token_type
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
            extra_fields={'task': task}
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
            extra_fields={'task': task}
        )
        slz.is_valid(raise_exception=True)
        user_id = slz.validated_data['user_id']
        try:
            TaskPerformersService.delete_performer(
                task=task,
                request_user=request.user,
                user_key=user_id,
                is_superuser=request.is_superuser,
                auth_type=request.token_type
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
            extra_fields={'task': task}
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
            extra_fields={'task': task}
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
                auth_type=request.token_type
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
            extra_fields={'task': task}
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
                data=request.data
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
            .prefetch_related('attachments',)
            .on_task(task.id)
            .type_in(WorkflowEventType.TASK_EVENTS)
        )
        qst = self.filter_queryset(qst)
        return self.paginated_response(qst)
