from typing import List

from celery import shared_task
from django.db import transaction

from src.authentication.enums import AuthTokenType
from src.processes.enums import WorkflowStatus
from src.processes.models.templates.template import (
    Template,
    TemplateVersion,
)
from src.processes.models.workflows.workflow import Workflow
from src.processes.services.workflow_permissions import (
    WorkflowPermissionService,
)
from src.processes.services.workflows.workflow_version import (
    WorkflowUpdateVersionService,
)
from src.processes.tasks.tasks import UserModel
from src.storage.tasks import (
    schedule_sync_workflow_attachment_permissions,
)


def _update_workflows(
    template_id: int,
    version: int,
    updated_by: int,
    sync: bool,
    auth_type: AuthTokenType,
    is_superuser: bool,
):
    template = Template.objects.by_id(template_id).first()
    if not template or template.version > version:
        return

    updated_by = UserModel.objects.get(id=updated_by)
    template_version = TemplateVersion.objects.filter(
        template_id=template_id,
        version=version,
    ).first()
    if template_version is None:
        return
    version_dict = template_version.data

    for _workflow in template.workflows.all().only('id'):
        with transaction.atomic():
            workflow = Workflow.objects.select_for_update().get(
                id=_workflow.id,
            )
            if not workflow.is_version_lower(version):
                continue
            if workflow.status == WorkflowStatus.DONE:
                template_owner_ids = Template.objects.filter(
                    id=workflow.template_id,
                ).get_owners_as_users()
                # Guardian: set change + TEMPLATE_OWNER view
                perm_svc = WorkflowPermissionService(workflow)
                perm_svc.set_view_and_change(
                    user_ids=list(template_owner_ids),
                )
                schedule_sync_workflow_attachment_permissions(
                    workflow.id,
                )
            else:
                version_service = WorkflowUpdateVersionService(
                    instance=workflow,
                    user=updated_by,
                    auth_type=auth_type,
                    is_superuser=is_superuser,
                    sync=sync,
                )
                version_service.update_from_version(
                    data=version_dict,
                    version=version,
                )


@shared_task(
    acks_late=True,
    autoretry_for=(Exception, ),
    retry_kwargs={
        'max_retries': 3,
        'countdown': 2,
    },
)
def update_workflows(**kwargs):
    _update_workflows(sync=True, **kwargs)


@shared_task(
    acks_late=True,
    autoretry_for=(Exception,),
    retry_kwargs={
        'max_retries': 3,
        'countdown': 5,
    },
)
def sync_workflow_performer_permissions(workflow_id: int):
    """Realign PERFORMER / PERFORMER_GROUP UOP rows for one
    workflow after bulk reassignment.

    Called asynchronously via on_commit so the main request
    returns faster.
    """
    try:
        workflow = Workflow.objects.get(
            id=workflow_id,
            is_deleted=False,
        )
    except Workflow.DoesNotExist:
        return
    WorkflowPermissionService(workflow).sync_performer_sources()
    schedule_sync_workflow_attachment_permissions(workflow_id)


@shared_task(
    acks_late=True,
    autoretry_for=(Exception,),
    retry_kwargs={
        'max_retries': 3,
        'countdown': 2,
    },
)
def update_workflow_owners(template_ids: List[int]):
    """Rebuild Guardian change_workflow when template owners change.

    Only updates TEMPLATE_OWNER / change rows via set_view_and_change.
    Performer UOP is unchanged when owners change — do not call
    sync_performer_sources here (avoids double work with reassign
    members sync and unnecessary load).
    """
    for template_id in template_ids:
        template_owner_ids = list(
            Template.objects.filter(
                id=template_id,
            ).get_owners_as_users(),
        )
        workflows = Workflow.objects.filter(
            template_id=template_id,
            is_deleted=False,
        ).only('id', 'account_id', 'template_id')
        for workflow in workflows:
            WorkflowPermissionService(workflow).set_view_and_change(
                user_ids=template_owner_ids,
            )
            schedule_sync_workflow_attachment_permissions(workflow.id)
