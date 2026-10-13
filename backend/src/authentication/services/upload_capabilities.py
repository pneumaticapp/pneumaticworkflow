import src.storage.messages as fs_messages
from typing import Optional
from uuid import UUID

from django.http import Http404
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied

from src.authentication.constants import (
    UPLOAD_CAPABILITY_TTL,
    UPLOAD_TOKEN_PREFIX,
)
from src.authentication.services.connections import ConnectionService
from src.authentication.tokens import create_token, get_digest, get_expiration
from src.mcp.enums import (
    McpScope,
)
from src.storage.enums import (
    UploadStatus,
)
from src.authentication.exceptions import (
    InactiveGrant,
)
from src.storage.services.exceptions import (
    UploadConflict,
)
from src.mcp.models import UploadCapability, UploadSession
from src.storage.services.upload_targets import UploadTargetService


class UploadCapabilityService:
    """Short-lived bearers letting storage write one upload session."""

    @classmethod
    def issue(cls, session: UploadSession) -> str:
        if (
            session.expires_at <= timezone.now()
            or session.status not in UploadStatus.OPEN
        ):
            raise UploadConflict(fs_messages.MSG_FS_0017)
        UploadTargetService.check_target(session=session)
        credential = create_token(prefix=UPLOAD_TOKEN_PREFIX)
        UploadCapability.objects.create(
            digest=get_digest(value=credential),
            session=session,
            expires_at=get_expiration(
                ttl=UPLOAD_CAPABILITY_TTL,
                limit=session.expires_at,
            ),
        )
        return credential

    @classmethod
    def get_active(
        cls,
        credential: str,
        session_id: Optional[UUID] = None,
    ) -> UploadCapability:
        capability = (
            UploadCapability.objects.select_related(
                'session__connection__user__account',
                'session__connection__account',
                'session__field',
                'session__field_template',
            )
            .filter(digest=get_digest(value=credential))
            .first()
        )
        if session_id is not None:
            session_id = UUID(str(session_id))
        if capability is None or not cls._is_active(
            capability=capability,
            session_id=session_id,
        ):
            raise InactiveGrant
        try:
            UploadTargetService.check_target(session=capability.session)
        except (PermissionDenied, NotFound, Http404) as ex:
            raise InactiveGrant from ex
        return capability

    @classmethod
    def _is_active(
        cls,
        capability: UploadCapability,
        session_id: Optional[UUID],
    ) -> bool:
        session = capability.session
        now = timezone.now()
        return (
            capability.expires_at > now
            and session.expires_at > now
            and session.status in UploadStatus.OPEN
            and (session_id is None or session.pk == session_id)
            and McpScope.FILE_WRITE in session.connection.scopes
            and ConnectionService.is_live(connection=session.connection)
        )
