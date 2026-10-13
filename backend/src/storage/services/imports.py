from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from django.db import transaction
from django.http import Http404
from django.utils import timezone
from rest_framework.exceptions import APIException

from src.accounts.models import Account
from src.authentication.services.connections import ConnectionService
from src.authentication.services.upload_capabilities import (
    UploadCapabilityService,
)
from src.storage.constants import (
    DISPATCH_BATCH_SIZE,
    IMPORT_MAX_ATTEMPTS,
    IMPORT_MAX_RUNNING_PER_ACCOUNT,
    LEASE_DURATION,
    RETRY_DELAY,
    STORAGE_IMPORT_PATH,
)
from src.storage.enums import (
    ImportJobState,
    UploadStatus,
)
from src.mcp.models import ImportJob, UploadSession
from src.storage.services.exceptions import (
    StorageUnavailable,
)
from src.storage.services.file_service import FileServiceClient
from src.storage.services.upload_sessions import UploadSessionService


@dataclass(frozen=True)
class ImportClaim:
    """A leased attempt; only its owner may finish or requeue the job."""

    attempt: int
    lease_until: datetime
    payload: dict


class ImportService:
    """Durable URL imports performed by storage with a fresh capability.

    The raw capability lives only in the claim and is never persisted.
    """

    @classmethod
    def get_due_session_ids(cls) -> list[UUID]:
        now = timezone.now()
        return list(
            ImportJob.objects.due(now=now).values_list(
                'session_id',
                flat=True,
            )[:DISPATCH_BATCH_SIZE],
        )

    @classmethod
    def process(cls, session_id: str):
        claim = cls._claim(session_id=session_id)
        if claim is None:
            return
        try:
            FileServiceClient.post_internal(
                path=STORAGE_IMPORT_PATH,
                payload=claim.payload,
            )
        except StorageUnavailable:
            cls._release(session_id=session_id, claim=claim, is_sent=False)
            return
        cls._release(session_id=session_id, claim=claim, is_sent=True)

    @classmethod
    @transaction.atomic
    def _claim(cls, session_id: str) -> Optional[ImportClaim]:
        """Lease the job or return None when there is nothing to run now."""
        job = (
            ImportJob.objects.select_for_update()
            .filter(session_id=session_id)
            .first()
        )
        if job is None or not cls._is_due(job=job):
            return None
        session = UploadSessionService.lock_session(session_id=session_id)
        if session.status in (UploadStatus.READY, UploadStatus.ATTACHED):
            job.state = ImportJobState.DONE
            job.save(update_fields=['state'])
            return None
        if (
            not ConnectionService.is_live(connection=session.connection)
            or session.expires_at <= timezone.now()
            or job.attempts >= IMPORT_MAX_ATTEMPTS
        ):
            cls._fail(job=job, session=session)
            return None
        if cls._is_account_busy(account_id=session.connection.account_id):
            cls._requeue(job=job)
            return None
        try:
            credential = UploadCapabilityService.issue(session=session)
        except (APIException, Http404):
            cls._fail(job=job, session=session)
            return None
        job.state = ImportJobState.RUNNING
        job.attempts += 1
        job.lease_until = timezone.now() + LEASE_DURATION
        job.save(update_fields=['state', 'attempts', 'lease_until'])
        return ImportClaim(
            attempt=job.attempts,
            lease_until=job.lease_until,
            payload={
                'credential': credential,
                'upload_session_id': str(session.pk),
                'url': session.source_url,
                'filename': session.filename,
            },
        )

    @classmethod
    @transaction.atomic
    def _release(cls, session_id: str, claim: ImportClaim, is_sent: bool):
        job = ImportJob.objects.select_for_update().get(session_id=session_id)
        if (
            job.state != ImportJobState.RUNNING
            or job.attempts != claim.attempt
            or job.lease_until != claim.lease_until
        ):
            return
        is_ready = (
            is_sent
            and UploadSession.objects.filter(
                pk=session_id,
                status__in=(UploadStatus.READY, UploadStatus.ATTACHED),
            ).exists()
        )
        if is_ready:
            job.state = ImportJobState.DONE
            job.lease_until = None
            job.save(update_fields=['state', 'lease_until'])
        else:
            cls._requeue(job=job)

    @classmethod
    def _is_due(cls, job: ImportJob) -> bool:
        now = timezone.now()
        return (
            job.state not in ImportJobState.FINISHED
            and not (
                job.state == ImportJobState.QUEUED
                and job.next_attempt_at > now
            )
            and not (job.lease_until and job.lease_until > now)
        )

    @classmethod
    def _is_account_busy(cls, account_id: int) -> bool:
        """Serialize claims per account to bound concurrent downloads."""
        Account.objects.select_for_update(no_key=True).get(pk=account_id)
        running = ImportJob.objects.filter(
            session__connection__account_id=account_id,
            state=ImportJobState.RUNNING,
            lease_until__gt=timezone.now(),
        ).count()
        return running >= IMPORT_MAX_RUNNING_PER_ACCOUNT

    @classmethod
    def _requeue(cls, job: ImportJob):
        job.state = ImportJobState.QUEUED
        job.lease_until = None
        job.next_attempt_at = timezone.now() + RETRY_DELAY
        job.save(update_fields=['state', 'lease_until', 'next_attempt_at'])

    @classmethod
    def _fail(cls, job: ImportJob, session: UploadSession):
        UploadSessionService.mark_failed(session=session)
        is_completed = UploadSession.objects.filter(
            pk=session.pk,
            status__in=(UploadStatus.READY, UploadStatus.ATTACHED),
        ).exists()
        job.state = (
            ImportJobState.DONE if is_completed else ImportJobState.FAILED
        )
        job.save(update_fields=['state'])
