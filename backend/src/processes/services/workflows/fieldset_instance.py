from decimal import Decimal, InvalidOperation
from typing import Dict

from django.contrib.auth import get_user_model

from src.processes.enums import FieldSetRuleType, FieldType
from src.processes.messages.fieldset import MSG_FS_0002
from src.processes.models.templates.kickoff import Kickoff
from src.processes.models.templates.task import TaskTemplate
from src.processes.models.workflows.fieldset import Fieldset, FieldSetRule
from src.processes.models.workflows.kickoff import KickoffValue
from src.processes.models.workflows.task import Task
from src.processes.models.workflows.workflow import Workflow
from src.processes.services.tasks.exceptions import TaskFieldException
from src.processes.services.tasks.field import TaskFieldService

UserModel = get_user_model()


def _sum_max_violation(fieldset: Fieldset) -> bool:
    rules = fieldset.rules.filter(
        is_deleted=False,
        type=FieldSetRuleType.SUM_MAX,
    )
    if not rules.exists():
        return False
    number_fields = list(
        fieldset.fields.filter(is_deleted=False, type=FieldType.NUMBER),
    )
    total = Decimal(0)
    for tf in number_fields:
        if tf.value not in (None, ''):
            try:
                total += Decimal(tf.value)
            except (InvalidOperation, TypeError, ValueError):
                continue
    for rule in rules:
        if not rule.value:
            continue
        try:
            threshold = Decimal(rule.value)
        except (InvalidOperation, TypeError, ValueError):
            continue
        if total > threshold:
            return True
    return False


def validate_fieldsets(fieldsets_qs):
    for fieldset in fieldsets_qs.filter(is_deleted=False):
        if _sum_max_violation(fieldset):
            first = (
                fieldset.fields.filter(
                    is_deleted=False,
                    type=FieldType.NUMBER,
                )
                .order_by('id')
                .first()
            )
            raise TaskFieldException(
                api_name=first.api_name if first else '',
                message=MSG_FS_0002,
            )


def create_kickoff_fieldsets_with_values(
    *,
    kickoff: Kickoff,
    kickoff_value: KickoffValue,
    workflow: Workflow,
    user: UserModel,
    fields_data: Dict,
):
    fields_data = fields_data or {}
    for fs_template in kickoff.fieldsets.all().order_by('id'):
        fieldset = Fieldset.objects.create(
            account_id=workflow.account_id,
            workflow=workflow,
            kickoff_value=kickoff_value,
            api_name=fs_template.api_name,
            name=fs_template.name,
            description=fs_template.description or '',
        )
        for rule_template in fs_template.rules.filter(is_deleted=False):
            FieldSetRule.objects.create(
                account_id=workflow.account_id,
                fieldset=fieldset,
                api_name=rule_template.api_name,
                type=rule_template.type,
                value=rule_template.value,
            )
        fields = fs_template.fields.all().order_by('-order', 'id')
        for field_template in fields:
            TaskFieldService(user=user).create(
                instance_template=field_template,
                workflow_id=workflow.id,
                kickoff_id=kickoff_value.id,
                fieldset_id=fieldset.id,
                value=fields_data.get(field_template.api_name),
            )


def ensure_task_fieldsets_and_fields(
    *,
    task: Task,
    user: UserModel,
) -> None:
    workflow = task.workflow
    if not workflow.template_id:
        return
    try:
        task_template = workflow.template.tasks.get(api_name=task.api_name)
    except TaskTemplate.DoesNotExist:
        return
    for fs_template in task_template.fieldsets.all().order_by('id'):
        if Fieldset.objects.filter(
            task=task,
            is_deleted=False,
        ).exists():
            continue
        fieldset = Fieldset.objects.create(
            account_id=workflow.account_id,
            workflow=workflow,
            task=task,
            api_name=fs_template.api_name,
            name=fs_template.name,
            description=fs_template.description,
        )
        for rule_template in fs_template.rules.filter(is_deleted=False):
            FieldSetRule.objects.create(
                account_id=workflow.account_id,
                fieldset=fieldset,
                api_name=rule_template.api_name,
                type=rule_template.type,
                value=rule_template.value,
            )
        fields = fs_template.fields.all().order_by('-order', 'id')
        for field_template in fields:
            TaskFieldService(user=user).create(
                instance_template=field_template,
                workflow_id=workflow.id,
                task_id=task.id,
                fieldset_id=fieldset.id,
                skip_value=True,
            )


def validate_task_fieldsets(*, task: Task) -> None:
    validate_fieldsets(
        Fieldset.objects.filter(task=task),
    )
