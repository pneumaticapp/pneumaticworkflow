from datetime import datetime

from django.db.models import Q, QuerySet

from src.storage.enums import (
    ImportJobState,
    UploadStatus,
)


class ImportJobQuerySet(QuerySet):

    def due(self, now: datetime) -> 'ImportJobQuerySet':
        """Queued jobs whose retry time came and runs with a lost lease."""
        return self.filter(
            Q(state=ImportJobState.QUEUED, next_attempt_at__lte=now)
            | Q(state=ImportJobState.RUNNING, lease_until__lte=now),
        )


class UploadSessionQuerySet(QuerySet):

    def with_stale_source_url(self, limit: int) -> list:
        """Finished sessions still holding the URL they imported from."""
        return list(
            self.filter(status__in=UploadStatus.FINISHED)
            .exclude(source_url='')
            .order_by('pk')
            .values_list('pk', flat=True)[:limit],
        )
