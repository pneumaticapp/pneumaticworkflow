from celery import shared_task

from src.storage.enums import AccessType


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

    Called after set_viewers() or set_owners() to ensure
    attachment permissions stay in sync with workflow access.

    Must run asynchronously via Celery to avoid blocking the
    main API thread — a workflow may have hundreds of attachments.
    """

    from src.processes.models.workflows.workflow import Workflow  # noqa: PLC0415
    from src.storage.models import Attachment  # noqa: PLC0415
    from src.storage.services.attachments import AttachmentService  # noqa: PLC0415

    try:
        workflow = Workflow.objects.get(
            id=workflow_id,
            is_deleted=False,
        )
    except Workflow.DoesNotExist:
        return

    service = AttachmentService()
    restricted_attachments = Attachment.objects.filter(
        workflow=workflow,
        access_type=AccessType.RESTRICTED,
    ).select_related('task')

    for att in restricted_attachments:
        service.reassign_restricted_permissions(att)
