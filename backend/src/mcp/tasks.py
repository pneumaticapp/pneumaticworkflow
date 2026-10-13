from celery import shared_task

from src.celery_app import periodic_lock
from src.authentication.services.pruning import CredentialPruneService
from src.storage.services.pruning import UploadPruneService


@shared_task
def prune_expired_state():
    with periodic_lock('mcp_prune_expired_state') as acquired:
        if not acquired:
            return
        CredentialPruneService.prune_expired_state()
        UploadPruneService.prune_expired_state()
