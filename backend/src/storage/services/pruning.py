from django.db import transaction
from django.utils import timezone

from src.mcp.models import ImportJob, UploadSession
from src.storage.constants import (
    UPLOAD_PRUNE_BATCH_SIZE,
    UPLOAD_STATE_RETENTION,
)
from src.storage.enums import ImportJobState, UploadStatus


class UploadPruneService:
    """Bounded cleanup of transfer state; keep storage deletion fences."""

    @classmethod
    @transaction.atomic
    def prune_expired_state(cls):
        now = timezone.now()
        cutoff = now - UPLOAD_STATE_RETENTION
        ids = UploadSession.objects.with_stale_source_url(
            limit=UPLOAD_PRUNE_BATCH_SIZE,
        )
        UploadSession.objects.filter(pk__in=ids).update(source_url='')
        job_ids = list(
            ImportJob.objects.filter(
                state__in=ImportJobState.FINISHED,
                session__expires_at__lte=cutoff,
            )
            .select_for_update(skip_locked=True, of=('self',))
            .order_by('session__expires_at', 'pk')
            .values_list('pk', flat=True)[:UPLOAD_PRUNE_BATCH_SIZE],
        )
        ImportJob.objects.filter(pk__in=job_ids).delete()
        session_ids = list(
            UploadSession.objects.filter(
                status=UploadStatus.ATTACHED,
                expires_at__lte=cutoff,
                importjob__isnull=True,
            )
            .select_for_update(skip_locked=True, of=('self',))
            .order_by('expires_at', 'pk')
            .values_list('pk', flat=True)[:UPLOAD_PRUNE_BATCH_SIZE],
        )
        UploadSession.objects.filter(pk__in=session_ids).delete()
