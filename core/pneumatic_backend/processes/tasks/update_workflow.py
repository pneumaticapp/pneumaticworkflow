from celery import shared_task
from django.db import transaction

from pneumatic_backend.processes.tasks.tasks import UserModel
from pneumatic_backend.processes.models import (
    Template,
    TemplateVersion,
    Workflow,
)
from pneumatic_backend.processes.api_v2.services.workflows\
    .workflow_version import (
        WorkflowUpdateVersionService
    )
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

    for workflow in template.workflows.running():
        with transaction.atomic():
            workflow = Workflow.objects.select_for_update().get(
                id=workflow.id
            )
            if not workflow.is_version_lower(version):
                return

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
