from typing import List

from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from pneumatic_backend.utils.validation import raise_validation_error
from pneumatic_backend.accounts.permissions import (
    UsersOverlimitedPermission,
    ExpiredSubscriptionPermission,
)
from pneumatic_backend.processes.models import (
    WorkflowEvent,
)
from pneumatic_backend.processes.serializers.comments import (
    CommentCreateSerializer,
    CommentReactionSerializer,
)
from pneumatic_backend.processes.api_v2.serializers.workflow.events import (
    WorkflowEventSerializer,
)
from pneumatic_backend.generics.mixins.views import CustomViewSetMixin
from pneumatic_backend.generics.permissions import (
    IsAuthenticated,
    PaymentCardPermission,
)

from pneumatic_backend.processes.permissions import (
    CommentEditPermission,
    CommentReactionPermission,
)
from pneumatic_backend.processes.api_v2.services import (
    CommentService,
)
from pneumatic_backend.processes.api_v2.services.exceptions import (
    CommentServiceException
)


class CommentViewSet(
    CustomViewSetMixin,
    GenericViewSet
):

    action_serializer_classes = {
        'partial_update': CommentCreateSerializer,
        'create_reaction': CommentReactionSerializer,
        'delete_reaction': CommentReactionSerializer,
    }

    def get_permissions(self):
        if self.action in (
            'partial_update',
            'destroy'
        ):
            return (
                IsAuthenticated(),
                PaymentCardPermission(),
                ExpiredSubscriptionPermission(),
                UsersOverlimitedPermission(),
                CommentEditPermission(),
            )
        elif self.action in (
            'watched',
            'create_reaction',
            'delete_reaction',
        ):
            return (
                IsAuthenticated(),
                PaymentCardPermission(),
                ExpiredSubscriptionPermission(),
                UsersOverlimitedPermission(),
                CommentReactionPermission(),
            )
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        qst = WorkflowEvent.objects.type_comment()
        if self.action in {'partial_update', 'destroy'}:
            qst = qst.by_user(user.id)
        return self.prefetch_queryset(qst)

    def prefetch_queryset(self, queryset, extra_fields: List[str] = None):
        if self.action in ('create_reaction', 'delete_reaction'):
            extra_fields = ['workflow']
        return super().prefetch_queryset(
            queryset=queryset,
            extra_fields=extra_fields
        )

    def partial_update(self, request, *args, **kwargs):
        comment_event = self.get_object()
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)
        service = CommentService(
            instance=comment_event,
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser
        )
        try:
            event = service.update(
                **slz.validated_data,
                force_save=True
            )
        except CommentServiceException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok(
            WorkflowEventSerializer(instance=event).data
        )

    def destroy(self, request, *args, **kwargs):
        comment_event = self.get_object()
        service = CommentService(
            instance=comment_event,
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser
        )
        try:
            event = service.delete()
        except CommentServiceException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok(
            WorkflowEventSerializer(instance=event).data
        )

    @action(methods=('post',), detail=True)
    def watched(self, request, *args, **kwargs):
        comment_event = self.get_object()
        service = CommentService(
            instance=comment_event,
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser
        )
        try:
            service.watched()
        except CommentServiceException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok()

    @action(methods=('post',), detail=True, url_path='create-reaction')
    def create_reaction(self, request, *args, **kwargs):
        comment_event = self.get_object()
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)
        service = CommentService(
            instance=comment_event,
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser
        )
        try:
            service.create_reaction(value=slz.validated_data['value'])
        except CommentServiceException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok()

    @action(methods=('post',), detail=True, url_path='delete-reaction')
    def delete_reaction(self, request, *args, **kwargs):
        comment_event = self.get_object()
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)
        service = CommentService(
            instance=comment_event,
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser
        )
        try:
            service.delete_reaction(value=slz.validated_data['value'])
        except CommentServiceException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok()
