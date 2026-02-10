from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet

from src.generics.mixins.views import CustomViewSetMixin
from src.generics.permissions import IsAuthenticated
from src.storage.models import Attachment
from src.storage.serializers import (
    AttachmentCheckPermissionSerializer,
    AttachmentListSerializer,
    AttachmentSerializer,
)
from src.storage.services.attachments import AttachmentService


class AttachmentViewSet(CustomViewSetMixin, GenericViewSet):
    """
    ViewSet for working with attachments.
    Provides endpoint for checking file access permissions.
    """

    serializer_class = AttachmentSerializer
    permission_classes = (IsAuthenticated,)
    queryset = Attachment.objects.all()

    def get_serializer_class(self):
        """Returns serializer class depending on action."""
        if self.action == 'check_permission':
            return AttachmentCheckPermissionSerializer
        if self.action == 'list':
            return AttachmentListSerializer
        return AttachmentSerializer

    def get_queryset(self):
        """Returns queryset considering user permissions."""
        if self.action == 'list':
            service = AttachmentService(user=self.request.user)
            return service.get_user_attachments(self.request.user)
        return self.queryset

    @action(
        methods=['POST'],
        detail=False,
        url_path='check-permission',
    )
    def check_permission(self, request, *args, **kwargs):
        """
        Checks user permission to access file.
        Used by file service for authorization.

        Returns:
        - 204: Access granted
        - 400: Validation error
        - 401: Not authenticated
        - 403: Access denied or file not found
        """
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)

        file_id = slz.validated_data['file_id']

        # Use service to check permissions
        service = AttachmentService(user=request.user)
        has_permission = service.check_user_permission(
            user_id=request.user.id,
            account_id=request.user.account_id,
            file_id=file_id,
        )

        if has_permission:
            return self.response_ok()
        return self.response_forbidden()

    def list(self, request, *args, **kwargs):
        """Returns list of attachments accessible to user."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return self.response_ok(serializer.data)
