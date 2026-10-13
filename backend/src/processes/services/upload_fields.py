from collections.abc import Callable
from typing import Any

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied

import src.processes.messages.workflow as workflow_messages
from src.accounts.permissions import (
    check_billing,
)
from src.processes.enums import FieldType, TaskStatus
from src.processes.models.templates.fields import FieldTemplate
from src.processes.models.templates.template import Template
from src.processes.models.workflows.fields import TaskField
from src.processes.models.workflows.task import Task
from src.processes.permissions import (
    check_task_performer,
    check_template_access,
)
from src.utils.validation import raise_validation_error
from src.storage.utils import extract_file_ids_from_values

UserModel = get_user_model()


class UploadFieldService:
    """Resolve the file field an upload is bound to and recheck access."""

    LINKED_FIELD_TYPES = (
        FieldType.FILE,
        FieldType.TEXT,
        FieldType.STRING,
        FieldType.URL,
    )

    @classmethod
    def get_kickoff_file_fields(
        cls,
        template: Template,
    ) -> dict[str, FieldTemplate]:
        return {
            field.api_name: field
            for field in template.fields.for_kickoff(
                template_id=template.pk,
            ).filter(type=FieldType.FILE)
        }

    @classmethod
    def get_task_file_names(cls, task: Task) -> set[str]:
        return set(
            TaskField.objects.for_task(task_id=task.pk)
            .filter(
                workflow=task.workflow,
                type=FieldType.FILE,
            )
            .values_list('api_name', flat=True),
        )

    @classmethod
    def get_task_linked_file_names(cls, task: Task) -> set[str]:
        return {
            field.api_name
            for field in TaskField.objects.for_task(task_id=task.pk).filter(
                workflow=task.workflow,
                type__in=cls.LINKED_FIELD_TYPES,
            )
            if field.type == FieldType.FILE
            or extract_file_ids_from_values(
                values=[field.value, field.markdown_value],
            )
        }

    @classmethod
    def map_file_values(
        cls,
        value: Any,
        names: set[str],
        transform: Callable[[str, Any], Any],
    ) -> Any:
        """Visit direct and fieldset values without interpreting file data."""
        if isinstance(value, list):
            return [
                cls.map_file_values(
                    value=item,
                    names=names,
                    transform=transform,
                )
                for item in value
            ]
        if not isinstance(value, dict):
            return value
        return {
            name: (
                transform(name, item)
                if name in names
                else cls.map_file_values(
                    value=item,
                    names=names,
                    transform=transform,
                )
            )
            for name, item in value.items()
        }

    @classmethod
    def contains_fields(cls, value: Any, names: set[str]) -> bool:
        if isinstance(value, dict):
            return bool(names.intersection(value)) or any(
                cls.contains_fields(value=item, names=names)
                for item in value.values()
            )
        if isinstance(value, list):
            return any(
                cls.contains_fields(value=item, names=names) for item in value
            )
        return False

    @classmethod
    def get_kickoff_template(
        cls,
        user: UserModel,
        template_id: int,
    ) -> Template:
        template = get_object_or_404(
            Template.objects.filter(account_id=user.account_id),
            pk=template_id,
        )
        check_template_access(user=user, template_id=template.pk)
        return template

    @classmethod
    def get_task_field(
        cls,
        user: UserModel,
        task_id: int,
        field_api_name: str,
    ) -> tuple[Task, TaskField]:
        task = get_object_or_404(
            Task.objects.select_related('workflow').filter(
                account_id=user.account_id,
                workflow__is_deleted=False,
            ),
            pk=task_id,
        )
        check_billing(user=user)
        check_task_performer(user=user, task_id=task.pk)
        if task.status != TaskStatus.ACTIVE:
            raise PermissionDenied
        fields = list(
            TaskField.objects.for_task(task_id=task.pk)
            .filter(
                Q(fieldset__isnull=True)
                | Q(
                    fieldset__is_deleted=False,
                    fieldset__account_id=user.account_id,
                    fieldset__workflow=task.workflow,
                    fieldset__task=task,
                ),
                workflow=task.workflow,
                account_id=user.account_id,
                api_name=field_api_name,
                type=FieldType.FILE,
                is_hidden=False,
            )
            .select_related('fieldset')[:2],
        )
        if len(fields) > 1:
            raise_validation_error(message=workflow_messages.MSG_PW_0092)
        if not fields:
            raise Http404('No TaskField matches the given query.')
        return task, fields[0]

    @classmethod
    def get_kickoff_field(
        cls,
        user: UserModel,
        template_id: int,
        field_api_name: str,
    ) -> tuple[Template, FieldTemplate]:
        template = cls.get_kickoff_template(
            user=user,
            template_id=template_id,
        )
        check_billing(user=user)
        field = get_object_or_404(
            FieldTemplate.objects.filter(
                Q(kickoff__template=template, kickoff__is_deleted=False)
                | Q(
                    fieldset__kickoff__template=template,
                    fieldset__kickoff__is_deleted=False,
                ),
                Q(fieldset__isnull=True)
                | Q(
                    fieldset__is_deleted=False,
                    fieldset__account_id=user.account_id,
                    fieldset__template=template,
                    fieldset__kickoff__template=template,
                ),
                template=template,
                account_id=user.account_id,
                api_name=field_api_name,
                type=FieldType.FILE,
                is_hidden=False,
            ),
        )
        return template, field
