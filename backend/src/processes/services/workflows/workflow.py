
from typing import Any, Dict, Iterable, Optional

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from src.analysis.actions import (
    WorkflowActions,
)
from src.analysis.services import AnalyticService
from src.authentication.enums import AuthTokenType
from src.processes.consts import WORKFLOW_NAME_LENGTH
from src.processes.utils.common import get_workflow_starter_name
from src.processes.models.templates.template import Template
from src.processes.models.workflows.fields import TaskField
from src.processes.models.workflows.workflow import Workflow
from src.processes.serializers.workflows.kickoff_value import (
    KickoffValueSerializer,
)
from src.processes.services.base import (
    BaseWorkflowService,
)
from src.processes.services.tasks.fields.field_ruleset_check import (
    FieldRuleCheckService,
)
from src.processes.services.tasks.task import TaskService
from src.processes.services.templates.integrations import (
    TemplateIntegrationsService,
)
from src.processes.services.urgent import UrgentService
from src.processes.utils.common import (
    contains_fields_vars,
    contains_workflow_id_var,
    insert_fields_values_to_text,
    string_abbreviation,
)
from src.processes.services.workflow_permissions import (
    WorkflowPermissionService,
)
from src.storage.tasks import (
    schedule_sync_workflow_attachment_permissions,
)
from src.storage.utils import (
    reassign_restricted_permissions_for_task,
    refresh_attachments,
)
from src.utils.dates import date_to_user_fmt

UserModel = get_user_model()


class WorkflowService(
    BaseWorkflowService,
):

    """ Parameters:
        template: template by which the workflow will be created
        kickoff_fields_data: dict with values for kickoff output fields
        workflow_starter:
            - for internal workflows: user who started the workflow
            - for external workflows: None
        user_provided_name:
            - for internal workflows: custom workflow name or None
            - for external workflows: None
        is_external: external workflow flag
    """

    def _create_workflow_name(
        self,
        template: Template,
        workflow_starter: Optional[UserModel] = None,
        user_provided_name: Optional[str] = None,
    ) -> str:

        """ Name filling priority:
            1. user_provided_name
            2. workflow_template_name
            3. template generic_name
            4. <current_date> <template name> """

        user = self.user
        values = {
            'date': date_to_user_fmt(date=timezone.now(), user=user),
            'template-name': template.name,
        }
        if workflow_starter:
            values.update(workflow_starter.get_dynamic_mapping())

        values['workflow-starter'] = get_workflow_starter_name(
            workflow_starter,
        )

        if user_provided_name:
            result = insert_fields_values_to_text(
                text=user_provided_name,
                fields_values=values,
            )
        elif template.wf_name_template:
            result = insert_fields_values_to_text(
                text=template.wf_name_template,
                fields_values=values,
            )
        elif template.generic_name:
            result = insert_fields_values_to_text(
                text=template.generic_name,
                fields_values=values,
            )
        else:
            result = f'{values["date"]} — {values["template-name"]}'
        return result

    def _create_instance(
        self,
        instance_template: Template,
        **kwargs,
    ):

        name = self._create_workflow_name(
            workflow_starter=kwargs.get('workflow_starter'),
            template=instance_template,
            user_provided_name=kwargs.get('user_provided_name'),
        )
        self.instance = Workflow.objects.create(
            template_id=instance_template.id,
            name=name,
            name_template=name,
            description=instance_template.description,
            account_id=instance_template.account_id,
            finalizable=instance_template.finalizable,
            status_updated=timezone.now(),
            version=instance_template.version,
            reminder_notification=instance_template.reminder_notification,
            completion_notification=instance_template.completion_notification,
            workflow_starter=kwargs.get('workflow_starter'),
            is_external=kwargs.get('is_external') or False,
            is_urgent=kwargs.get('is_urgent') or False,
            due_date=kwargs.get('due_date'),
            ancestor_task=kwargs.get('ancestor_task'),
        )

        name_changed = False
        name_template_changed = False
        if contains_workflow_id_var(self.instance.name_template):
            self.instance.name = insert_fields_values_to_text(
                text=self.instance.name_template,
                fields_values={'workflow-id': str(self.instance.id)},
            )
            self.instance.name_template = self.instance.name
            name_changed, name_template_changed = True, True

        # TODO replace KickoffValueSerializer to KickoffValueService
        kickoff = instance_template.kickoff_instance
        kickoff_value_slz = KickoffValueSerializer(
            data={
                'account_id': instance_template.account.id,
                'workflow': self.instance.id,
                'kickoff': kickoff.id,
                'fields_data': kwargs.get('kickoff_fields_data', {}),
            },
            context={'user': self.user},
        )
        kickoff_value_slz.is_valid(raise_exception=True)
        kickoff_value_slz.save()

        # insert kickoff fields values
        if contains_fields_vars(self.instance.name):
            fields_values = self.instance.get_kickoff_fields_values()
            self.instance.name = insert_fields_values_to_text(
                text=self.instance.name_template,
                fields_values=fields_values,
            )
            name_changed = True

        # After insert fields vars
        if len(self.instance.name) > WORKFLOW_NAME_LENGTH:
            self.instance.name = string_abbreviation(
                name=self.instance.name,
                length=WORKFLOW_NAME_LENGTH,
            )
            name_changed = True

        if name_changed or name_template_changed:
            update_fields = []
            if name_changed:
                update_fields.append('name')
            if name_template_changed:
                update_fields.append('name_template')
            self.instance.save(update_fields=update_fields)
        return self.instance

    def _create_related(
        self,
        instance_template: Template,
        **kwargs,
    ):

        for task_template in instance_template.tasks.order_by('number'):
            task_service = TaskService(user=self.user)
            task_service.create(
                instance_template=task_template,
                workflow=self.instance,
                redefined_performer=kwargs.get('redefined_performer'),
            )
        self.update_owners()
        self.apply_field_rulesets()

        # Update attachments for workflow
        refresh_attachments(self.instance, self.user)

    def apply_field_rulesets(
        self,
        rulesets: Optional[Iterable] = None,
    ):

        """ Call inside the transaction that saved the kickoff values and
            before the workflow event: a failed kickoff validator must roll
            the change back. Task field validators are checked on complete.
        """

        if rulesets is None:
            rulesets = self.instance.field_rulesets.for_kickoff().with_groups()
        rulesets = list(rulesets)
        if not rulesets:
            return
        user = self.user or self.instance.account.get_owner()
        fields_by_api_name = {
            field.api_name: field
            for field in TaskField.objects.for_rules_check(self.instance.id)
        }
        rules_by_field: dict = {}
        for ruleset in rulesets:
            rules_by_field.setdefault(ruleset.field_id, []).append(ruleset)
        fields_to_update = []
        for field_rules in rules_by_field.values():
            field = fields_by_api_name[field_rules[0].field.api_name]
            was_hidden = field.is_hidden
            service = FieldRuleCheckService(field)
            service.apply_rulesets(
                field_rules,
                timezone_name=user.timezone,
                fields_by_api_name=fields_by_api_name,
            )
            if field.is_hidden != was_hidden:
                fields_to_update.append(field)
        if fields_to_update:
            TaskField.objects.bulk_update(fields_to_update, ['is_hidden'])

    def _create_actions(self, **kwargs):
        if kwargs.get('anonymous_id'):
            AnalyticService.workflows_started(
                workflow=self.instance,
                auth_type=self.auth_type,
                is_superuser=self.is_superuser,
                anonymous_id=kwargs['anonymous_id'],
            )
        else:
            AnalyticService.workflows_started(
                workflow=self.instance,
                auth_type=self.auth_type,
                is_superuser=self.is_superuser,
                user=self.user,
            )
        if self.instance.is_urgent:
            AnalyticService.workflows_urgent(
                workflow=self.instance,
                auth_type=self.auth_type,
                is_superuser=self.is_superuser,
                user=self.user,
                action=WorkflowActions.marked,
            )

        if self.auth_type == AuthTokenType.API:
            service = TemplateIntegrationsService(
                account=self.user.account,
                is_superuser=self.is_superuser,
                user=self.user,
            )
            service.api_request(
                template=self.instance.template,
                user_agent=kwargs.get('user_agent'),
            )

    def update(
        self,
        validated_data: Dict[str, Any],
    ) -> Workflow:
        update_kickoff_kwargs = {}
        update_tasks_kwargs = {}
        update_instance_kwargs = {}

        is_urgent = validated_data.get('is_urgent')
        is_urgent_changed = (
            is_urgent is not None
            and is_urgent != self.instance.is_urgent
        )
        name = validated_data.get('name')
        kickoff_fields_data = validated_data.get('kickoff')
        if name:
            update_instance_kwargs['name'] = name
            update_instance_kwargs['name_template'] = name

        if (
            'due_date_tsp' in validated_data
            and validated_data['due_date_tsp'] != self.instance.due_date
        ):
            update_instance_kwargs['due_date'] = (
                validated_data['due_date_tsp']
            )

        if is_urgent_changed:
            update_instance_kwargs['is_urgent'] = is_urgent
            update_tasks_kwargs['is_urgent'] = is_urgent
        if kickoff_fields_data:
            update_kickoff_kwargs['fields_data'] = kickoff_fields_data
            update_tasks_kwargs['fields_data'] = kickoff_fields_data

        with transaction.atomic():
            if update_instance_kwargs:
                self.instance = self._partial_update_workflow(
                    **update_instance_kwargs,
                )
            if update_kickoff_kwargs:
                self._update_kickoff_value(**update_kickoff_kwargs)
                self.apply_field_rulesets()
                if contains_fields_vars(self.instance.name_template):
                    fields_values = (
                        self.instance.get_kickoff_fields_values()
                    )
                    self.instance.name = insert_fields_values_to_text(
                        text=self.instance.name_template,
                        fields_values=fields_values,
                    )
                    self.instance.save(update_fields=['name'])

            if update_tasks_kwargs:
                self._update_tasks(
                    is_urgent=is_urgent,
                    update_fields_values=bool(kickoff_fields_data),
                )
            if is_urgent_changed:
                UrgentService.resolve(
                    workflow=self.instance,
                    user=self.user,
                )
        return self.instance

    def _update_kickoff_value(
        self,
        fields_data: Dict[str, Any],
    ):
        kickoff_slz = KickoffValueSerializer(
            data={
                'fields_data': fields_data,
            },
            instance=self.instance.kickoff_instance,
            partial=True,
            context={
                'user': self.user,
            },
        )
        kickoff_slz.is_valid(raise_exception=True)
        return kickoff_slz.save()

    def _partial_update_workflow(self, **kwargs) -> Workflow:
        update_fields = []
        if 'name' in kwargs:
            self.instance.name = string_abbreviation(
                name=kwargs['name'],
                length=WORKFLOW_NAME_LENGTH,
            )
            self.instance.name_template = kwargs['name']
            update_fields.append('name')
            update_fields.append('name_template')
        if 'is_urgent' in kwargs:
            self.instance.is_urgent = kwargs['is_urgent']
            update_fields.append('is_urgent')
        if 'due_date' in kwargs:
            self.instance.due_date = kwargs['due_date']
            update_fields.append('due_date')
        if update_fields:
            self.instance.save(update_fields=update_fields)
        return self.instance

    def _update_tasks(
        self,
        update_fields_values: bool,
        is_urgent: Optional[bool] = None,
    ):
        tasks = self.instance.tasks.exclude_pending().order_by('id')
        if is_urgent is not None and not update_fields_values:
            tasks.update(is_urgent=is_urgent)
        elif update_fields_values:
            fields_values = self.instance.get_fields_markdown_values()
            for task in tasks:
                task_service = TaskService(
                    instance=task,
                    user=self.user,
                )
                if is_urgent is not None:
                    task_service.partial_update(is_urgent=is_urgent)
                task_service.insert_fields_values(fields_values)
                if task.is_active:
                    task_service.set_due_date_from_template()
                    task.update_performers()
                    reassign_restricted_permissions_for_task(
                        task=task,
                        user=self.user,
                    )

    def partial_update(
        self,
        force_save=False,
        **update_kwargs,
    ):
        result = super().partial_update(
            force_save=force_save,
            **update_kwargs,
        )
        if 'description' in update_kwargs:
            refresh_attachments(self.instance, self.user)
        return result

    def update_owners(self):
        user_ids = Template.objects.filter(
            id=self.instance.template_id,
        ).get_owners_as_users()
        WorkflowPermissionService(self.instance).set_view_and_change(
            user_ids=user_ids,
        )
        schedule_sync_workflow_attachment_permissions(
            self.instance.id,
        )
