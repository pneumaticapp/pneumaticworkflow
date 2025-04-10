from celery import shared_task
from django.db import transaction
from typing import List

from pneumatic_backend.processes.enums import WorkflowStatus
from pneumatic_backend.processes.tasks.tasks import UserModel
from pneumatic_backend.processes.models import (
    Template,
    TemplateVersion,
    Workflow,
)
from pneumatic_backend.processes.queries import (
    UpdateWorkflowOwnersQuery,
    UpdateWorkflowMemberQuery
)
from pneumatic_backend.processes.api_v2.services.workflows\
    .workflow_version import (
        WorkflowUpdateVersionService
    )
from pneumatic_backend.executor import RawSqlExecutor
from pneumatic_backend.authentication.enums import AuthTokenType


def _update_workflows(
    template_id: int,
    version: int,
    updated_by: int,
    sync: bool,
    auth_type: AuthTokenType,
    is_superuser: bool
):
    template = Template.objects.by_id(template_id).first()
    if not template or template.version > version:
        return

    updated_by = UserModel.objects.get(id=updated_by)
    version_dict = TemplateVersion.objects.filter(
        template_id=template_id,
        version=version,
    ).first().data

    for workflow in template.workflows.all():
        with transaction.atomic():
            workflow = Workflow.objects.select_for_update().get(
                id=workflow.id
            )
            if not workflow.is_version_lower(version):
                return
            if workflow.status == WorkflowStatus.DONE:
                template_owner_ids = Template.objects.filter(
                    id=workflow.template_id
                ).get_owners_as_users()
                workflow.owners.set(template_owner_ids)
            else:
                version_service = WorkflowUpdateVersionService(
                    instance=workflow,
                    user=updated_by,
                    auth_type=auth_type,
                    is_superuser=is_superuser,
                    sync=sync
                )
                version_service.update_from_version(
                    data=version_dict,
                    version=version
                )


@shared_task(
    acks_late=True,
    autoretry_for=(Exception, ),
    retry_kwargs={
        'max_retries': 3,
        'countdown': 2,
    },
)
def update_workflows(*args, **kwargs):
    _update_workflows(sync=True, *args, **kwargs)


@shared_task(
    acks_late=True,
    autoretry_for=(Exception,),
    retry_kwargs={
        'max_retries': 3,
        'countdown': 2,
    },
)
def update_workflow_owners(template_ids: List[int]):
    with transaction.atomic():
        Workflow.owners.through.objects.filter(
            workflow__template_id__in=template_ids
        ).delete()
        for template_id in template_ids:
            query_workflow = UpdateWorkflowOwnersQuery(
                template_id=template_id
            )
            RawSqlExecutor.execute(*query_workflow.insert_sql())
            query_member = UpdateWorkflowMemberQuery(
                template_id=template_id
            )
            RawSqlExecutor.execute(*query_member.insert_sql())
