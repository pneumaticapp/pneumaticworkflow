from collections.abc import Callable
import src.storage.messages as fs_messages
from src.processes.services.upload_fields import UploadFieldService
from dataclasses import dataclass
from uuid import NAMESPACE_URL, UUID, uuid5

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied

from src.authentication.services.connections import ConnectionService
from src.authentication.services.upload_capabilities import (
    UploadCapabilityService,
)
from src.storage.constants import (
    CLEANUP_FILE_ID_NAMESPACE,
    CLEANUP_MIN_AGE,
    UPLOAD_SESSION_TTL,
)
from src.storage.enums import (
    ImportJobState,
    UploadStatus,
    UploadTargetType,
)
from src.mcp.enums import (
    McpScope,
)
from src.authentication.exceptions import (
    InactiveGrant,
)
from src.storage.services.exceptions import (
    IneligibleCleanup,
    UploadConflict,
)
from src.mcp.models import (
    Connection,
    Delegation,
    ImportJob,
    UploadSession,
)
from src.storage.services.upload_targets import UploadTargetService
from src.processes.models.workflows.fields import TaskField
from src.processes.services.tasks.field import TaskFieldService
from src.storage.file_metadata import canonical_content_type
from src.storage.models import Attachment
from src.storage.utils import (
    extract_file_links_from_text,
    get_file_service_file_url,
)
from src.utils.validation import raise_validation_error

UserModel = get_user_model()


@dataclass(frozen=True)
class IssuedUpload:
    credential: str
    session: UploadSession


class UploadSessionService:
    @classmethod
    def get_session(
        cls,
        user: UserModel,
        delegation: Delegation | None,
        session_id: UUID | str,
        lock: bool = False,
    ) -> UploadSession:
        try:
            session_id = UUID(str(session_id))
        except ValueError:
            raise_validation_error(message=fs_messages.MSG_FS_0015)
        query = UploadSession.objects.select_related(
            'connection__user__account',
            'connection__account',
            'field',
            'field_template',
        )
        if lock:
            query = query.select_for_update(of=('self',))
        session = get_object_or_404(
            query,
            pk=session_id,
            connection__user_id=user.pk,
            connection__account_id=user.account_id,
        )
        if (
            isinstance(delegation, Delegation)
            and session.connection_id != delegation.connection_id
            and not ConnectionService.is_same_identity(
                first=session.connection,
                second=delegation.connection,
            )
        ):
            raise NotFound(fs_messages.MSG_FS_0016)
        return session

    @classmethod
    def get_status(cls, session: UploadSession) -> str:
        if not ConnectionService.is_live(connection=session.connection):
            return UploadStatus.REVOKED
        if (
            session.expires_at <= timezone.now()
            and session.status != UploadStatus.ATTACHED
        ):
            return UploadStatus.EXPIRED
        return session.status

    @classmethod
    def is_attachable(cls, session: UploadSession) -> bool:
        return (
            session.status == UploadStatus.READY
            and session.expires_at > timezone.now()
        )

    @classmethod
    @transaction.atomic
    def create(
        cls,
        user: UserModel,
        delegation: Delegation,
        data: dict,
    ) -> IssuedUpload:
        if (
            not isinstance(delegation, Delegation)
            or McpScope.FILE_WRITE not in delegation.scopes
        ):
            raise PermissionDenied
        target = {}
        if data['target_type'] == UploadTargetType.TASK:
            target['task'], target['field'] = (
                UploadFieldService.get_task_field(
                    user=user,
                    task_id=data['task_id'],
                    field_api_name=data['field_api_name'],
                )
            )
        else:
            target['template'], target['field_template'] = (
                UploadFieldService.get_kickoff_field(
                    user=user,
                    template_id=data['template_id'],
                    field_api_name=data['field_api_name'],
                )
            )
        session = UploadSession.objects.create(
            connection=delegation.connection,
            target_type=data['target_type'],
            filename=data['filename'],
            content_type=data['content_type'],
            size=data['size'],
            expires_at=timezone.now() + UPLOAD_SESSION_TTL,
            **target,
        )
        return IssuedUpload(
            credential=UploadCapabilityService.issue(session=session),
            session=session,
        )

    @classmethod
    @transaction.atomic
    def create_upload_token(
        cls,
        user: UserModel,
        delegation: Delegation | None,
        session_id: UUID | str,
    ) -> IssuedUpload:
        session = cls.get_session(
            user=user,
            delegation=delegation,
            session_id=session_id,
            lock=True,
        )
        return IssuedUpload(
            credential=UploadCapabilityService.issue(session=session),
            session=session,
        )

    @classmethod
    @transaction.atomic
    def queue_import(
        cls,
        user: UserModel,
        delegation: Delegation | None,
        session_id: UUID | str,
        url: str,
    ) -> UploadSession:
        session = cls.get_session(
            user=user,
            delegation=delegation,
            session_id=session_id,
            lock=True,
        )
        UploadTargetService.check_target(session=session)
        if (
            session.status != UploadStatus.PENDING
            or session.expires_at <= timezone.now()
        ):
            raise UploadConflict(fs_messages.MSG_FS_0022)
        session.source_url = url
        session.status = UploadStatus.IMPORTING
        session.save(update_fields=['source_url', 'status'])
        ImportJob.objects.create(
            session=session,
            next_attempt_at=timezone.now(),
        )
        # Import after service initialization to avoid the task import cycle.
        from src.storage.tasks import import_upload  # noqa: PLC0415

        transaction.on_commit(
            lambda: import_upload.delay(str(session.pk)),
            robust=True,
        )
        return session

    @classmethod
    @transaction.atomic
    def attach(
        cls,
        user: UserModel,
        delegation: Delegation | None,
        session_id: UUID | str,
        task_id: int,
    ) -> UploadSession:
        session = cls.get_session(
            user=user,
            delegation=delegation,
            session_id=session_id,
            lock=True,
        )
        if (
            session.target_type != UploadTargetType.TASK
            or session.task_id != task_id
        ):
            raise PermissionDenied
        UploadTargetService.check_target(session=session)
        if not cls.is_attachable(session=session):
            raise UploadConflict(fs_messages.MSG_FS_0023)
        field = TaskField.objects.select_for_update().get(
            pk=session.field_id,
        )
        links = extract_file_links_from_text(text=field.markdown_value)
        links.append(cls.get_link(session=session))
        TaskFieldService(user=user, instance=field).partial_update(
            value=links,
        )
        cls.mark_attached(session=session)
        return session

    @classmethod
    @transaction.atomic
    def consume(
        cls,
        user: UserModel,
        delegation: Delegation | None,
        session_id: UUID | str,
        is_target: Callable[[UploadSession], bool],
    ) -> str:
        """Consume inside the transaction that stores the resulting link."""
        session = cls.get_session(
            user=user,
            delegation=delegation,
            session_id=session_id,
            lock=True,
        )
        if not is_target(session) or not cls.is_attachable(session=session):
            raise PermissionDenied
        UploadTargetService.check_target(session=session)
        link = cls.get_link(session=session)
        cls.mark_attached(session=session)
        return link

    @classmethod
    def get_link(cls, session: UploadSession) -> str:
        url = get_file_service_file_url(file_id=session.file_id)
        if not url:
            raise_validation_error(message=fs_messages.MSG_FS_0024)
        return f'[{session.filename}]({url})'

    @classmethod
    def mark_attached(cls, session: UploadSession):
        session.status = UploadStatus.ATTACHED
        session.save(update_fields=['status'])

    @classmethod
    @transaction.atomic
    def complete_upload(cls, data: dict) -> UploadSession:
        try:
            capability = UploadCapabilityService.get_active(
                credential=data['credential'],
                session_id=data['upload_session_id'],
            )
        except InactiveGrant as ex:
            raise PermissionDenied from ex
        session = cls.lock_session(session_id=capability.session_id)
        now = timezone.now()
        if capability.expires_at <= now or session.expires_at <= now:
            raise PermissionDenied
        UploadTargetService.check_target(session=session)
        content_type = canonical_content_type(value=data['content_type'])
        if session.status == UploadStatus.READY:
            cls._check_same_completion(
                session=session,
                data=data,
                content_type=content_type,
            )
            return session
        if session.status not in (
            UploadStatus.PENDING,
            UploadStatus.IMPORTING,
        ):
            raise UploadConflict(fs_messages.MSG_FS_0019)
        is_import = session.status == UploadStatus.IMPORTING
        if (
            session.filename != data['name']
            or data['size'] > settings.MCP_MAX_IMPORT_BYTES
            or (
                not is_import
                and (
                    session.size != data['size']
                    or session.content_type != content_type
                )
            )
        ):
            raise UploadConflict(fs_messages.MSG_FS_0020)
        session.size = data['size']
        session.content_type = content_type
        session.file_id = data['file_id']
        session.status = UploadStatus.READY
        session.source_url = ''
        session.save(
            update_fields=[
                'file_id',
                'status',
                'size',
                'content_type',
                'source_url',
            ],
        )
        return session

    @classmethod
    @transaction.atomic
    def authorize_cleanup(cls, data: dict):
        """Allow storage to delete an abandoned upload exactly once."""
        connection_id = (
            UploadSession.objects.filter(pk=data['upload_session_id'])
            .values_list('connection_id', flat=True)
            .first()
        )
        if connection_id is None:
            raise IneligibleCleanup
        Connection.objects.select_for_update().get(pk=connection_id)
        session = (
            UploadSession.objects.select_related(
                'connection',
            )
            .select_for_update(of=('self',))
            .get(pk=data['upload_session_id'])
        )
        if not cls._is_abandoned(session=session, data=data):
            raise IneligibleCleanup
        session.status = UploadStatus.CLEANED
        session.file_id = data['file_id']
        session.source_url = ''
        session.save(update_fields=['status', 'file_id', 'source_url'])

    @classmethod
    def _check_same_completion(
        cls,
        session: UploadSession,
        data: dict,
        content_type: str,
    ):
        """A retried completion must describe the stored file exactly."""
        if (
            session.file_id != data['file_id']
            or session.filename != data['name']
            or session.size != data['size']
            or session.content_type != content_type
        ):
            raise UploadConflict(fs_messages.MSG_FS_0018)

    @classmethod
    def _is_abandoned(cls, session: UploadSession, data: dict) -> bool:
        now = timezone.now()
        return (
            cls._get_cleanup_file_id(session=session) == data['file_id']
            and session.connection.account_id == data['account_id']
            and session.connection.user_id == data['user_id']
            and session.expires_at <= now
            and session.created_at <= now - CLEANUP_MIN_AGE
            and session.status != UploadStatus.ATTACHED
            and not ImportJob.objects.filter(
                session=session,
                state__in=ImportJobState.ACTIVE,
            ).exists()
            and not Attachment.all_objects.filter(
                file_id=data['file_id'],
            ).exists()
        )

    @classmethod
    def _get_cleanup_file_id(cls, session: UploadSession) -> str:
        """Storage names a never-completed upload by a derived UUID."""
        return session.file_id or str(
            uuid5(NAMESPACE_URL, f'{CLEANUP_FILE_ID_NAMESPACE}{session.pk}'),
        )

    @classmethod
    def lock_session(cls, session_id: UUID | str) -> UploadSession:
        """Lock the connection before its session, as storage callbacks do.

        Call inside a transaction. This also serializes completion and
        import failure, so a successful upload cannot be overwritten.
        """
        connection_id = UploadSession.objects.values_list(
            'connection_id',
            flat=True,
        ).get(pk=session_id)
        Connection.objects.select_for_update().get(pk=connection_id)
        return (
            UploadSession.objects.select_related(
                'connection__user__account',
                'connection__account',
            )
            .select_for_update(of=('self',))
            .get(pk=session_id)
        )

    @classmethod
    def mark_failed(cls, session: UploadSession) -> bool:
        """Fail only an unfinished upload, including for a stale caller."""
        return bool(
            UploadSession.objects.filter(
                pk=session.pk,
                status__in=(UploadStatus.PENDING, UploadStatus.IMPORTING),
            ).update(
                status=UploadStatus.FAILED,
                error=fs_messages.MSG_FS_0025,
                source_url='',
            ),
        )
