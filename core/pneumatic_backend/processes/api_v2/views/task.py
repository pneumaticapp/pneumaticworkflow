from typing import List
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet
from rest_framework.generics import ListAPIView

from pneumatic_backend.analytics.services import AnalyticService
from pneumatic_backend.generics.permissions import (
    UserIsAuthenticated,
    IsAuthenticated,
    PaymentCardPermission,
)
from pneumatic_backend.accounts.enums import UserType
from pneumatic_backend.processes.permissions import (
    TaskWorkflowMemberPermission,
    TaskTemplateOwnerPermission,
    GuestTaskPermission,
)
from pneumatic_backend.accounts.permissions import (
    UsersOverlimitedPermission,
    UserIsAdminOrAccountOwner,
    ExpiredSubscriptionPermission,
)
from pneumatic_backend.generics.mixins.views import (
    CustomViewSetMixin,
)
from pneumatic_backend.processes.models import (
    Task,
    TaskForList
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
        TaskGuestPerformerSerializer
    )
from pneumatic_backend.processes.api_v2.services.task.exceptions import (
    PerformersServiceException,
    TaskServiceException,
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


UserModel = get_user_model()


class TasksListView(ListAPIView):
    serializer_class = TaskListSerializer
    permission_classes = (
        UserIsAuthenticated,
        PaymentCardPermission,
        ExpiredSubscriptionPermission,
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
                user_id=user.id,
                page='tasks',
                search_text=search_text,
                is_superuser=request.is_superuser,
                auth_type=request.token_type
            )
        return super().list(request, *args, **kwargs)


class TaskViewSet(
    CustomViewSetMixin,
    BaseIdentifyMixin,
    GenericViewSet,
):
    serializer_class = TaskSerializer

    def get_permissions(self):
        if self.action == 'retrieve':
            return (
                IsAuthenticated(),
                PaymentCardPermission(),
                ExpiredSubscriptionPermission(),
                TaskWorkflowMemberPermission(),
                GuestTaskPermission(),
            )
        elif self.action in (
            'create_performer',
            'delete_performer',
            'create_guest_performer',
            'delete_guest_performer',
            'due_date',
        ):
            return (
                UserIsAuthenticated(),
                UserIsAdminOrAccountOwner(),
                TaskTemplateOwnerPermission(),
                PaymentCardPermission(),
                UsersOverlimitedPermission(),
                ExpiredSubscriptionPermission(),
            )
        return super().get_permissions()

    action_serializer_classes = {
        'retrieve': TaskSerializer,
        'create_performer': TaskPerformerSerializer,
        'delete_performer': TaskPerformerSerializer,
        'create_guest_performer': TaskGuestPerformerSerializer,
        'delete_guest_performer': TaskGuestPerformerSerializer,
        'due_date': DueDateSerializer,
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
        return qst

    def prefetch_queryset(self, queryset, extra_fields: List[str] = None):
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                'sub_workflows__template__template_owners',
                'checklists',
                'output',
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
                is_superuser=request.is_superuser
            )
        except PerformersServiceException as ex:
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
                user_key=user_id
            )
        except PerformersServiceException as ex:
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
                is_superuser=request.is_superuser
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
                user_key=email
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
            due_date = request_slz.validated_data['due_date']
        else:
            due_date = None
        service = TaskService(user=request.user, instance=task)
        try:
            service.set_due_date_directly(value=due_date)
        except TaskServiceException as ex:
            raise_validation_error(message=ex.message)
        else:
            return self.response_ok()
