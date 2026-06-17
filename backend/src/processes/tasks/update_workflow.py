from typing import List

from celery import shared_task
from django.db import transaction

from src.authentication.enums import AuthTokenType
from src.processes.enums import WorkflowStatus
from src.processes.models.templates.template import (
    Template,
    TemplateVersion,
)
from src.processes.models.workflows.task import TaskPerformer
from src.processes.models.workflows.workflow import Workflow
from src.processes.services.workflow_permissions import (
    WorkflowPermissionService,
)
from src.processes.services.workflows.workflow_version import (
    WorkflowUpdateVersionService,
)
from src.processes.tasks.tasks import UserModel


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
    version_dict = TemplateVersion.objects.filter(
        template_id=template_id,
        version=version,
    ).first().data

    for _workflow in template.workflows.all().only('id'):
        with transaction.atomic():
            workflow = Workflow.objects.select_for_update().get(
                id=_workflow.id,
            )
            if not workflow.is_version_lower(version):
                return
            if workflow.status == WorkflowStatus.DONE:
                template_owner_ids = Template.objects.filter(
                    id=workflow.template_id,
                ).get_owners_as_users()
                # Guardian: set owners for completed workflow
                WorkflowPermissionService.set_owners(
                    workflow, list(template_owner_ids),
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
        'countdown': 2,
    },
)
def update_workflow_owners(template_ids: List[int]):
    """Rebuild Guardian permissions when template owners change.

    For each workflow belonging to the given templates:
    1. Set manage_workflow + view_workflow for current template owners
    2. Grant view_workflow to all task performers
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
        )
        for workflow in workflows:
            with transaction.atomic():
                # Set owners (clears old manage + sets new manage + view)
                WorkflowPermissionService.set_owners(
                    workflow, template_owner_ids,
                )
                # Grant view to all task performers
                performer_ids = list(
                    TaskPerformer.objects
                    .filter(
                        task__workflow=workflow,
                        task__is_deleted=False,
                    )
                    .exclude_directly_deleted()
                    .get_user_ids_set(),
                )
                viewer_only = set(performer_ids) - set(template_owner_ids)
                if viewer_only:
                    WorkflowPermissionService.grant_view_bulk(
                        list(viewer_only), workflow,
                    )
