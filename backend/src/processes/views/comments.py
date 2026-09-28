from typing import List, Optional

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet

from src.accounts.permissions import (
    BillingPlanPermission,
    ExpiredSubscriptionPermission,
    UsersOverlimitedPermission,
)
from src.generics.mixins.views import CustomViewSetMixin
from src.generics.permissions import (
    DenyAll,
    IsAuthenticated,
)
from src.openapi import (
    ACCESS_COMMENT_EDIT,
    ACCESS_COMMENT_REACTION,
    EMPTY,
    FORBIDDEN,
    NOT_FOUND,
    UNAUTHORIZED,
    VALIDATION_ERROR,
)
from src.processes.models.workflows.event import WorkflowEvent
from src.processes.permissions import (
    CommentEditPermission,
    CommentReactionPermission,
)
from src.processes.serializers.comments import (
    CommentCreateSerializer,
    CommentReactionSerializer,
)
from src.processes.serializers.workflows.events import (
    WorkflowEventSerializer,
)
from src.processes.services.events import (
    CommentService,
)
from src.processes.services.exceptions import (
    CommentServiceException,
)
from src.utils.validation import raise_validation_error


class CommentViewSet(
    CustomViewSetMixin,
    GenericViewSet,
):

    serializer_class = WorkflowEventSerializer
    action_serializer_classes = {
        'partial_update': CommentCreateSerializer,
        'create_reaction': CommentReactionSerializer,
        'delete_reaction': CommentReactionSerializer,
    }

    def get_permissions(self):
        if self.action in (
            'partial_update',
            'destroy',
        ):
            return (
                IsAuthenticated(),
                BillingPlanPermission(),
                ExpiredSubscriptionPermission(),
                UsersOverlimitedPermission(),
                CommentEditPermission(),
            )
        if self.action in (
            'watched',
            'create_reaction',
            'delete_reaction',
        ):
            return (
                IsAuthenticated(),
                BillingPlanPermission(),
                ExpiredSubscriptionPermission(),
                UsersOverlimitedPermission(),
                CommentReactionPermission(),
            )
        return (DenyAll(),)

    def get_queryset(self):
        user = self.request.user
        qst = (
            WorkflowEvent.objects
            .select_related('workflow')
            .type_comment()
        )
        if self.action in {'partial_update', 'destroy'}:
            qst = qst.by_user(user.id)
        return self.prefetch_queryset(qst)

    def prefetch_queryset(
        self,
        queryset,
        extra_fields: Optional[List[str]] = None,
    ):
        if self.action in ('create_reaction', 'delete_reaction'):
            extra_fields = ['workflow']
        return super().prefetch_queryset(
            queryset=queryset,
            extra_fields=extra_fields,
        )

    @extend_schema(
        tags=['Workflows'],
        summary='Update comment',
        description=ACCESS_COMMENT_EDIT,
        request=CommentCreateSerializer,
        responses={
            200: WorkflowEventSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    def partial_update(self, request, *args, **kwargs):
        comment_event = self.get_object()
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)
        service = CommentService(
            instance=comment_event,
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser,
        )
        try:
            event = service.update(
                **slz.validated_data,
                force_save=True,
            )
        except CommentServiceException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok(
            WorkflowEventSerializer(instance=event).data,
        )

    @extend_schema(
        tags=['Workflows'],
        summary='Delete comment',
        description=ACCESS_COMMENT_EDIT,
        responses={
            200: WorkflowEventSerializer,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    def destroy(self, request, *args, **kwargs):
        comment_event = self.get_object()
        service = CommentService(
            instance=comment_event,
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser,
        )
        try:
            event = service.delete()
        except CommentServiceException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok(
            WorkflowEventSerializer(instance=event).data,
        )

    @extend_schema(
        tags=['Workflows'],
        summary='Mark comment as watched',
        description=ACCESS_COMMENT_REACTION,
        responses={
            200: EMPTY,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    @action(methods=('post',), detail=True)
    def watched(self, request, *args, **kwargs):
        comment_event = self.get_object()
        service = CommentService(
            instance=comment_event,
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser,
        )
        try:
            service.watched()
        except CommentServiceException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok()

    @extend_schema(
        tags=['Workflows'],
        summary='Add reaction to comment',
        description=ACCESS_COMMENT_REACTION,
        request=CommentReactionSerializer,
        responses={
            200: EMPTY,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    @action(methods=('post',), detail=True, url_path='create-reaction')
    def create_reaction(self, request, *args, **kwargs):
        comment_event = self.get_object()
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)
        service = CommentService(
            instance=comment_event,
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser,
        )
        try:
            service.create_reaction(value=slz.validated_data['value'])
        except CommentServiceException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok()

    @extend_schema(
        tags=['Workflows'],
        summary='Remove reaction from comment',
        description=ACCESS_COMMENT_REACTION,
        request=CommentReactionSerializer,
        responses={
            200: EMPTY,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    @action(methods=('post',), detail=True, url_path='delete-reaction')
    def delete_reaction(self, request, *args, **kwargs):
        comment_event = self.get_object()
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)
        service = CommentService(
            instance=comment_event,
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser,
        )
        try:
            service.delete_reaction(value=slz.validated_data['value'])
        except CommentServiceException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok()
