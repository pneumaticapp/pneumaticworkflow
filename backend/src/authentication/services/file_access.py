from typing import Optional
from uuid import UUID

from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from src.accounts.permissions import (
    check_billing,
)
from src.authentication.constants import (
    FILE_AUTHORIZATION_TTL,
)
from src.authentication.exceptions import (
    InvalidMcpToken,
)
from src.authentication.services.connections import ConnectionService
from src.authentication.services.delegation import DelegationService
from src.authentication.services.upload_capabilities import (
    UploadCapabilityService,
)
from src.authentication.tokens import get_expiration
from src.mcp.constants import (
    FILE_SERVICE_FILES_PATH,
)
from src.storage.enums import (
    FileOperation,
    UploadStatus,
)
from src.mcp.enums import (
    McpAudience,
    McpScope,
    McpTool,
)
from src.authentication.exceptions import (
    InactiveGrant,
)
from src.mcp.models import (
    Connection,
    Delegation,
    FileAuthorization,
    UploadCapability,
)
from src.storage.file_metadata import encoded_file_id
from src.storage.services.attachments import AttachmentService


class FileAccessService:
    """Authorize delegated file access and restricted upload credentials."""

    @classmethod
    def authorize_upload(
        cls,
        credential: str,
        operation: str,
        session_id: Optional[UUID] = None,
        connection_id: Optional[UUID] = None,
    ) -> UploadCapability:
        capability = UploadCapabilityService.get_active(
            credential=credential,
            session_id=session_id,
        )
        session = capability.session
        if (
            operation == FileOperation.UPLOAD
            and session.status == UploadStatus.IMPORTING
        ):
            raise InactiveGrant
        if connection_id not in (None, session.connection_id):
            raise InactiveGrant
        return capability

    @classmethod
    def authorize_file(
        cls,
        operation: str,
        file_id: Optional[str] = None,
        credential: Optional[str] = None,
        connection_id: Optional[UUID] = None,
        authorization_id: Optional[UUID] = None,
    ) -> FileAuthorization:
        """Grant a short file authorization to a delegated request.

        A download repeats with the issued `authorization_id` instead of
        the one-request delegation credential.
        """
        if not file_id:
            raise InactiveGrant
        if credential:
            delegation = cls._get_file_delegation(
                credential=credential,
                operation=operation,
                file_id=file_id,
            )
            connection = delegation.connection
            if connection_id not in (None, connection.pk):
                raise InactiveGrant
        else:
            authorization = cls._get_download_authorization(
                operation=operation,
                file_id=file_id,
                connection_id=connection_id,
                authorization_id=authorization_id,
            )
            connection = authorization.connection
        cls._check_file_permission(connection=connection, file_id=file_id)
        if credential:
            authorization = FileAuthorization.objects.create(
                connection=connection,
                source_token=delegation.source_token,
                file_id=file_id,
                expires_at=get_expiration(
                    ttl=FILE_AUTHORIZATION_TTL,
                    limit=delegation.source_token.expires,
                ),
            )
        return authorization

    @classmethod
    def _get_file_delegation(
        cls,
        credential: str,
        operation: str,
        file_id: str,
    ) -> Delegation:
        try:
            delegation = DelegationService.get_delegation(
                credential=credential,
            )
        except InvalidMcpToken as ex:
            raise InactiveGrant from ex
        path = FILE_SERVICE_FILES_PATH + encoded_file_id(value=file_id)
        tool = McpTool.GET_FILE_METADATA
        if operation == FileOperation.DOWNLOAD:
            path += '/download-ticket'
            tool = McpTool.CREATE_DOWNLOAD_TICKET
        if (
            delegation.audience != McpAudience.FILES
            or delegation.path != path
            or delegation.operation != tool
        ):
            raise InactiveGrant
        return delegation

    @classmethod
    def _get_download_authorization(
        cls,
        operation: str,
        file_id: str,
        connection_id: Optional[UUID],
        authorization_id: Optional[UUID],
    ) -> FileAuthorization:
        if operation != FileOperation.DOWNLOAD or not authorization_id:
            raise InactiveGrant
        authorization = (
            FileAuthorization.objects.select_related(
                'connection__user__account',
                'connection__account',
                'source_token',
            )
            .filter(
                pk=authorization_id,
                connection_id=connection_id,
                file_id=file_id,
            )
            .first()
        )
        if authorization is None or not cls._is_active_authorization(
            authorization=authorization,
        ):
            raise InactiveGrant
        return authorization

    @classmethod
    def _is_active_authorization(
        cls,
        authorization: FileAuthorization,
    ) -> bool:
        connection = authorization.connection
        source = authorization.source_token
        return (
            authorization.expires_at > timezone.now()
            and ConnectionService.is_live(connection=connection)
            and DelegationService.is_valid_source_token(
                token=source,
                connection=connection,
            )
            and McpScope.FILE_READ in source.scope.split()
            and DelegationService.is_bound_token(
                token=source,
                connection=connection,
            )
        )

    @classmethod
    def _check_file_permission(cls, connection: Connection, file_id: str):
        if McpScope.FILE_READ not in connection.scopes:
            raise InactiveGrant
        try:
            check_billing(user=connection.user)
        except PermissionDenied as ex:
            raise InactiveGrant from ex
        is_allowed = AttachmentService(
            user=connection.user,
        ).check_user_permission(
            user_id=connection.user_id,
            account_id=connection.account_id,
            file_id=file_id,
        )
        if not is_allowed:
            raise InactiveGrant
