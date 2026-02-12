from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import GenericViewSet

from src.generics.mixins.views import CustomViewSetMixin
from src.generics.permissions import IsAuthenticated
from src.storage.models import Attachment
from src.storage.queries import AttachmentListQuery
from src.storage.serializers import (
    AttachmentCheckPermissionSerializer,
    AttachmentListSerializer,
    AttachmentSerializer,
)
from src.storage.services.attachments import AttachmentService


class AttachmentViewSet(
    ListModelMixin,
    CustomViewSetMixin,
    GenericViewSet,
):
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
        query = AttachmentListQuery(user=request.user)
        self.queryset = Attachment.objects.execute_raw(query)
        return super().list(request, *args, **kwargs)
