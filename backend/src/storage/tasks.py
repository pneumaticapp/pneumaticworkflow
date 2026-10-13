from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.db.models import Q

from src.celery_app import periodic_lock
from src.storage.constants import (
    CLEANUP_BATCH_SIZE,
    STORAGE_CLEANUP_PATH,
)
from src.storage.services.imports import ImportService
from src.storage.services.file_service import FileServiceClient
from src.processes.models.workflows.workflow import Workflow
from src.storage.enums import AccessType
from src.storage.models import Attachment
from src.storage.services.attachments import AttachmentService


def schedule_sync_workflow_attachment_permissions(
    workflow_id: int,
):
    """Enqueue attachment ACL sync after the current DB TX commits.

    Safe with or without an open atomic block: Django runs the
    callback immediately when there is no active transaction.
    """
    transaction.on_commit(
        lambda wid=workflow_id: (
            sync_workflow_attachment_permissions.delay(wid)
        ),
    )


@shared_task(
    acks_late=True,
    autoretry_for=(Exception,),
    retry_kwargs={
        'max_retries': 3,
        'countdown': 5,
    },
)
def sync_workflow_attachment_permissions(workflow_id: int):
    """Recalculate access_attachment for all restricted attachments
    in a workflow after viewer/owner changes.

    Called after view/change permission updates to ensure
    attachment permissions stay in sync with workflow access.

    Must run asynchronously via Celery to avoid blocking the
    main API thread — a workflow may have hundreds of attachments.
    Prefer ``schedule_sync_workflow_attachment_permissions`` so the
    task is not enqueued before the surrounding transaction commits.

    Also rebuilds shared TEMPLATE attachments for the workflow's
    template (desired-set across all live workflows).
    """

    try:
        workflow = Workflow.objects.get(
            id=workflow_id,
            is_deleted=False,
        )
    except Workflow.DoesNotExist:
        return

    service = AttachmentService()
    # Task description files often have workflow_id=NULL (only task_id).
    # Event files usually set workflow_id, but include event__workflow
    # for safety. distinct() avoids duplicates when several FKs match.
    restricted_attachments = Attachment.objects.filter(
        Q(workflow=workflow)
        | Q(task__workflow=workflow)
        | Q(event__workflow=workflow),
        access_type=AccessType.RESTRICTED,
    ).distinct().select_related('task')

    for att in restricted_attachments:
        service.reassign_restricted_permissions(att)

    if workflow.template_id:
        service.rebuild_template_attachment_permissions(
            workflow.template_id,
        )


@shared_task(
    name='src.mcp.tasks.import_upload',
    soft_time_limit=80,
    time_limit=85,
)
def import_upload(session_id: str):
    ImportService.process(session_id=session_id)


@shared_task(name='src.mcp.tasks.dispatch_pending_imports')
def dispatch_pending_imports():
    if not settings.MCP_ENABLED:
        return
    with periodic_lock('mcp_dispatch_pending_imports') as acquired:
        if not acquired:
            return
        for session_id in ImportService.get_due_session_ids():
            import_upload.delay(str(session_id))


@shared_task(name='src.mcp.tasks.cleanup_uploads')
def cleanup_uploads():
    if not settings.MCP_ENABLED:
        return
    with periodic_lock('mcp_cleanup_uploads') as acquired:
        if not acquired:
            return
        FileServiceClient.post_internal(
            path=STORAGE_CLEANUP_PATH,
            payload={'limit': CLEANUP_BATCH_SIZE},
        )
