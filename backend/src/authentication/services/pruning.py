from django.utils import timezone

from src.authentication.constants import (
    PRUNE_BATCH_SIZE,
)
from src.mcp.models import (
    AuthorizationRequest,
    CodeBinding,
    Delegation,
    FileAuthorization,
    LoginCode,
    UploadCapability,
)


class CredentialPruneService:

    """Bounded batches keep each run short; queued work is never pruned."""

    EXPIRING_MODELS = (
        Delegation,
        LoginCode,
        CodeBinding,
        AuthorizationRequest,
        UploadCapability,
        FileAuthorization,
    )

    @classmethod
    def prune_expired_state(cls):
        now = timezone.now()
        for model in cls.EXPIRING_MODELS:
            ids = model.objects.expired(now=now, limit=PRUNE_BATCH_SIZE)
            model.objects.filter(pk__in=ids).delete()
