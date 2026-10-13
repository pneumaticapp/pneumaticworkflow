from src.storage.services.attachments import AttachmentService
from src.storage.services.upload_sessions import UploadSessionService
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from src.authentication.services.mcp_auth import StorageAuthentication
from src.storage.enums import (
    FileOperation,
)
from src.authentication.exceptions import (
    InactiveGrant,
)
from src.storage.services.exceptions import (
    IneligibleCleanup,
)
from src.mcp.serializers.files import (
    AttachmentResponseSerializer,
    CleanupSerializer,
    FileGrantSerializer,
    FileValidationSerializer,
    UploadCompletionSerializer,
    UploadGrantSerializer,
)
from src.mcp.serializers.uploads import UploadCompletedResponseSerializer
from src.authentication.services.file_access import FileAccessService
from src.mcp.views.base import (
    BusinessView,
)
from src.authentication.views.mcp import (
    EnabledMixin,
)


@extend_schema(exclude=True)
class FileValidationView(EnabledMixin, APIView):
    authentication_classes = (StorageAuthentication,)
    permission_classes = (AllowAny,)

    def post(self, request: Request):
        serializer = FileValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        operation = data['operation']
        try:
            if operation in FileOperation.CAPABILITY_OPERATIONS:
                grant = FileAccessService.authorize_upload(
                    credential=data.get('credential', ''),
                    operation=operation,
                    session_id=data.get('upload_session_id'),
                    connection_id=data.get('connection_id'),
                )
                body = UploadGrantSerializer(
                    grant,
                    context={'operation': operation},
                ).data
            else:
                grant = FileAccessService.authorize_file(
                    operation=operation,
                    file_id=data.get('file_id'),
                    credential=data.get('credential'),
                    connection_id=data.get('connection_id'),
                    authorization_id=data.get('authorization_id'),
                )
                body = FileGrantSerializer(
                    grant,
                    context={'operation': operation},
                ).data
        except InactiveGrant:
            return Response({'active': False})
        return Response(body)


@extend_schema(exclude=True)
class UploadCompletionView(FileValidationView):
    def post(self, request: Request):
        serializer = UploadCompletionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = UploadSessionService.complete_upload(
            data=serializer.validated_data,
        )
        return Response(UploadCompletedResponseSerializer(session).data)


@extend_schema(exclude=True)
class UploadCleanupView(FileValidationView):
    def post(self, request: Request):
        serializer = CleanupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            UploadSessionService.authorize_cleanup(
                data=serializer.validated_data,
            )
        except IneligibleCleanup:
            return Response({'eligible': False})
        return Response({'eligible': True})


@extend_schema(tags=['MCP'], responses={200: OpenApiTypes.OBJECT})
class AttachmentDetailView(BusinessView):
    def get(self, request: Request, attachment_id: int):
        return Response(
            AttachmentResponseSerializer(
                AttachmentService(user=request.user).get_for_user(
                    attachment_id=attachment_id,
                ),
            ).data,
        )
