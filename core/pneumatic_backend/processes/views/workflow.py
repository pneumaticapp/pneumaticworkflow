from django.db import transaction
from rest_framework.decorators import action
from rest_framework.generics import (
    get_object_or_404
)
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.mixins import ListModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet
from pneumatic_backend.analytics.services import AnalyticService
from pneumatic_backend.utils.validation import raise_validation_error
from pneumatic_backend.accounts.permissions import (
    UsersOverlimitedPermission,
    UserIsAdminOrAccountOwner,
    ExpiredSubscriptionPermission,
)
from pneumatic_backend.analytics.actions import (
    WorkflowActions
)
from pneumatic_backend.generics.filters import PneumaticFilterBackend
from pneumatic_backend.processes.paginations import WorkflowPagination
from pneumatic_backend.processes.models import (
    Workflow,
    WorkflowEvent,
)
from pneumatic_backend.processes.permissions import (
    WorkflowTemplateOwnerPermission,
    WorkflowMemberPermission,
    UserTaskCompletePermission,
    GuestWorkflowPermission,
    GuestTaskCompletePermission,
)
from pneumatic_backend.processes.serializers.comments import (
    CommentCreateSerializer,
)
from pneumatic_backend.processes.serializers.workflow import (
    WorkflowDetailsSerializer,
    WorkflowCompleteSerializer,
    WorkflowRevertSerializer,
    WorkflowReturnToTaskSerializer,
    WorkflowFinishSerializer,
    WorkflowUpdateSerializer,
    WorkflowListSerializer,
    WorkflowListFilterSerializer,
    WorkflowFieldsSerializer,
    WorkflowSnoozeSerializer,
)
from pneumatic_backend.processes.api_v2.serializers.workflow.events import (
    WorkflowEventSerializer,
)
from pneumatic_backend.accounts.enums import UserType
from pneumatic_backend.generics.mixins.views import CustomViewSetMixin
from pneumatic_backend.generics.permissions import (
    UserIsAuthenticated,
    IsAuthenticated,
    PaymentCardPermission,
)
from pneumatic_backend.processes.filters import (
    WorkflowFieldsFilter,
    WorkflowEventFilter,
)
from pneumatic_backend.processes.services.exceptions import (
    WorkflowActionServiceException
)
from pneumatic_backend.processes.services.workflow_action import (
    WorkflowActionService
)
from pneumatic_backend.processes.api_v2.services import (
    CommentService,
)
from pneumatic_backend.processes.api_v2.services.exceptions import (
    CommentServiceException
)
from pneumatic_backend.processes.api_v2.services.task.exceptions import (
    TaskFieldException
)
from pneumatic_backend.processes.enums import WorkflowEventType


class WorkflowViewSet(
    CustomViewSetMixin,
    ListModelMixin,
    UpdateModelMixin,
    GenericViewSet
):

    pagination_class = WorkflowPagination
    filter_backends = (PneumaticFilterBackend, )
    action_serializer_classes = {
        'retrieve': WorkflowDetailsSerializer,
        'comment': CommentCreateSerializer,
        'complete': WorkflowCompleteSerializer,
        'revert': WorkflowRevertSerializer,
        'return_to': WorkflowReturnToTaskSerializer,
        'finish': WorkflowFinishSerializer,
        'partial_update': WorkflowUpdateSerializer,
        'list': WorkflowListSerializer,
        'fields': WorkflowFieldsSerializer,
        'snooze': WorkflowDetailsSerializer,
        'events': WorkflowEventSerializer,
    }
    action_filterset_classes = {
        'fields': WorkflowFieldsFilter,
        'events': WorkflowEventFilter,
    }

    action_paginator_classes = {
        'events': LimitOffsetPagination,
    }

    def get_serializer_context(self, **kwargs):
        context = super().get_serializer_context(**kwargs)
        context['user'] = self.request.user
        context['account'] = self.request.user.account
        context['is_superuser'] = self.request.is_superuser
        context['auth_type'] = self.request.token_type
        return context

    def get_queryset(self):
        user = self.request.user
        queryset = Workflow.objects.on_account(user.account_id)
        if self.action in ('list', 'fields'):
            queryset = queryset.with_member(user)
        return self.prefetch_queryset(queryset)

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

    def get_permissions(self):
        if self.action in ('list', 'fields'):
            return (
                UserIsAuthenticated(),
                UserIsAdminOrAccountOwner(),
                PaymentCardPermission(),
                ExpiredSubscriptionPermission(),
            )
        elif self.action == 'retrieve':
            return (
                UserIsAuthenticated(),
                PaymentCardPermission(),
                ExpiredSubscriptionPermission(),
                WorkflowMemberPermission(),
            )
        elif self.action in (
            'destroy',
            'terminate',
            'resume',
            'snooze',
            'finish',
            'return_to',
        ):
            return (
                UserIsAuthenticated(),
                UserIsAdminOrAccountOwner(),
                PaymentCardPermission(),
                ExpiredSubscriptionPermission(),
                WorkflowTemplateOwnerPermission(),
                UsersOverlimitedPermission(),
            )
        elif self.action == 'partial_update':
            return (
                UserIsAuthenticated(),
                PaymentCardPermission(),
                ExpiredSubscriptionPermission(),
                WorkflowTemplateOwnerPermission(),
                UsersOverlimitedPermission(),
            )
        elif self.action == 'comment':
            return (
                IsAuthenticated(),
                PaymentCardPermission(),
                ExpiredSubscriptionPermission(),
                UsersOverlimitedPermission(),
                GuestWorkflowPermission(),
                WorkflowMemberPermission(),
            )
        elif self.action == 'complete':
            return (
                IsAuthenticated(),
                PaymentCardPermission(),
                ExpiredSubscriptionPermission(),
                UsersOverlimitedPermission(),
                GuestTaskCompletePermission(),
                UserTaskCompletePermission(),
            )
        elif self.action == 'revert':
            return (
                UserIsAuthenticated(),
                PaymentCardPermission(),
                ExpiredSubscriptionPermission(),
                UsersOverlimitedPermission(),
                UserTaskCompletePermission(),
            )
        elif self.action == 'events':
            return (
                IsAuthenticated(),
                PaymentCardPermission(),
                ExpiredSubscriptionPermission(),
                GuestWorkflowPermission(),
                WorkflowMemberPermission(),
            )
        return super().get_permissions()

    def list(self, request, *args, **kwargs):
        filter_slz = WorkflowListFilterSerializer(data=request.GET)
        filter_slz.is_valid(raise_exception=True)
        queryset = Workflow.objects.raw_list_query(
            **filter_slz.validated_data,
            account_id=request.user.account_id,
            user_id=request.user.id
        )

        search_text = filter_slz.validated_data.get('search')
        if search_text:
            AnalyticService.search_search(
                user_id=request.user.id,
                page='processes',
                search_text=search_text,
                is_superuser=getattr(request, 'is_superuser', False),
                auth_type=request.token_type,
            )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return self.response_ok(serializer.data)

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
            data=request.data
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
            user_id=request.user.id,
        )
        if is_urgent_changed:
            AnalyticService.workflows_urgent(
                workflow=workflow,
                auth_type=request.token_type,
                is_superuser=request.is_superuser,
                user_id=request.user.id,
                action=(
                    WorkflowActions.marked if is_urgent else
                    WorkflowActions.unmarked
                )
            )
        return self.response_ok(
            WorkflowDetailsSerializer(instance=workflow).data
        )

    @action(methods=['post'], detail=True)
    def comment(self, request, *args, **kwargs):
        workflow = self.get_object()
        slz = self.get_serializer(
            data=request.data,
            extra_fields={'workflow': workflow}
        )
        slz.is_valid(raise_exception=True)
        service = CommentService(
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser
        )
        try:
            event = service.create(
                workflow=workflow,
                **slz.validated_data
            )
        except CommentServiceException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok(
            WorkflowEventSerializer(instance=event).data
        )

    @action(methods=['post'], detail=True, url_path='task-complete')
    def complete(self, request, *args, **kwargs):
        workflow = self.get_object()
        serializer = self.get_serializer(
            data=request.data,
            extra_fields={'workflow': workflow}
        )
        serializer.is_valid(raise_exception=True)
        service = WorkflowActionService(
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser
        )
        try:
            with transaction.atomic():
                service.complete_current_task_for_user(
                    workflow=workflow,
                    fields_values=serializer.validated_data.get('output')
                )
        except WorkflowActionServiceException as ex:
            raise_validation_error(message=ex.message)
        except TaskFieldException as ex:
            raise_validation_error(
                message=ex.message,
                api_name=ex.api_name
            )
        workflow.refresh_from_db()
        return self.response_ok()

    @action(methods=['post'], detail=True, url_path='task-revert')
    def revert(self, request, pk=None):
        queryset = self.get_queryset().running()
        workflow = get_object_or_404(queryset, id=pk)
        serializer = self.get_serializer(
            instance=workflow,
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.response_ok()

    @action(methods=['post'], detail=True, url_path='return-to')
    def return_to(self, request, pk=None):
        queryset = self.get_queryset()
        workflow = get_object_or_404(queryset, id=pk)
        serializer = self.get_serializer(
            instance=workflow,
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.response_ok()

    def destroy(self, request, *args, **kwargs):
        service = WorkflowActionService(
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser
        )
        try:
            service.terminate_workflow(workflow=self.get_object())
        except WorkflowActionServiceException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok()

    @action(methods=['post'], detail=True, url_path='close')
    def terminate(self, request, *args, **kwargs):
        # Deprecated. Will be removed in my.pneumatic.app/workflows/34225/
        service = WorkflowActionService(
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser
        )
        try:
            service.terminate_workflow(workflow=self.get_object())
        except WorkflowActionServiceException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok()

    @action(methods=['post'], detail=True)
    def resume(self, request, *args, **kwargs):
        service = WorkflowActionService(
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser
        )
        try:
            service.force_resume_workflow(workflow=self.get_object())
        except WorkflowActionServiceException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok()

    @action(methods=['post'], detail=True)
    def finish(self, request, *args, **kwargs):
        workflow = self.get_object()
        serializer = self.get_serializer(
            instance=workflow,
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        AnalyticService.workflows_ended(
            user=request.user,
            workflow=workflow,
            auth_type=request.token_type,
            is_superuser=request.is_superuser
        )
        return self.response_ok()

    @action(methods=['get'], detail=False)
    def fields(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        return self.paginated_response(queryset)

    @action(methods=['post'], detail=True)
    def snooze(self, request, *args, **kwargs):
        request_slz = WorkflowSnoozeSerializer(data=request.data)
        request_slz.is_valid(raise_exception=True)
        workflow = self.get_object()
        service = WorkflowActionService(
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser
        )
        try:
            service.force_delay_workflow(
                workflow=workflow,
                date=request_slz.validated_data['date']
            )
        except WorkflowActionServiceException as ex:
            raise_validation_error(message=ex.message)
        serializer = self.get_serializer(workflow)
        return self.response_ok(serializer.data)

    @action(methods=['get'], detail=True)
    def events(self, request, *args, **kwargs):
        workflow = self.get_object()
        qst = WorkflowEvent.objects.prefetch_related(
            'attachments',
        ).on_workflow(
            workflow.id
        ).exclude_type(WorkflowEventType.RUN)
        if self.request.user.type == UserType.GUEST:
            qst = qst.by_task(
                self.request.task_id
            ).exclude(type=WorkflowEventType.TASK_START)
        qst = self.filter_queryset(qst)
        return self.paginated_response(qst)
