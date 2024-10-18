
from typing import Optional
from django.utils import timezone
from django.contrib.auth import get_user_model
from pneumatic_backend.processes.api_v2.services.base import (
    BaseWorkflowService,
)
from pneumatic_backend.processes.models import (
    Template,
    Workflow,
)
from pneumatic_backend.utils.dates import date_to_user_fmt
from pneumatic_backend.processes.utils.common import (
    string_abbreviation,
    insert_fields_values_to_text,
    insert_kickoff_fields_vars,
    contains_fields_vars,
)
from pneumatic_backend.processes.serializers.kickoff_value import (
    KickoffValueSerializer
)
from pneumatic_backend.processes.consts import WORKFLOW_NAME_LENGTH
from pneumatic_backend.processes.api_v2.services.templates.integrations \
    import TemplateIntegrationsService
from pneumatic_backend.processes.api_v2.services.task.task import TaskService
from pneumatic_backend.analytics.actions import (
    WorkflowActions
)
from pneumatic_backend.processes.tasks.webhooks import (
    send_workflow_started_webhook,
)
from pneumatic_backend.analytics.services import AnalyticService
from pneumatic_backend.authentication.enums import AuthTokenType


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
        user_provided_name: Optional[str] = None
    ) -> str:

        """ Name filling priority:
            1. user_provided_name
            2. workflow_template_name
            3. template generic_name
            4. <current_date> <template name> """

        user = self.user
        values = {
            'date': date_to_user_fmt(date=timezone.now(), user=user),
            'template-name': template.name
        }
        if workflow_starter:
            values.update(workflow_starter.get_dynamic_mapping())

        if user_provided_name:
            result = insert_fields_values_to_text(
                text=user_provided_name,
                fields_values=values
            )
        elif template.wf_name_template:
            result = insert_fields_values_to_text(
                text=template.wf_name_template,
                fields_values=values
            )
        elif template.generic_name:
            result = insert_fields_values_to_text(
                text=template.generic_name,
                fields_values=values
            )
        else:
            result = f'{values["date"]} — {values["template-name"]}'
        return result

    def _create_instance(
        self,
        instance_template: Template,
        **kwargs
    ):

        name = self._create_workflow_name(
            workflow_starter=kwargs.get('workflow_starter'),
            template=instance_template,
            user_provided_name=kwargs.get('user_provided_name'),
        )
        self.instance = Workflow.objects.create(
            template_id=instance_template.id,
            tasks_count=instance_template.tasks_count,
            name=name,
            name_template=name,
            description=instance_template.description,
            account_id=instance_template.account_id,
            finalizable=instance_template.finalizable,
            status_updated=timezone.now(),
            version=instance_template.version,
            workflow_starter=kwargs.get('workflow_starter'),
            is_external=kwargs.get('is_external') or False,
            is_urgent=kwargs.get('is_urgent') or False,
            due_date=kwargs.get('due_date'),
            ancestor_task=kwargs.get('ancestor_task')
        )

        # TODO replace KickoffValueSerializer to KickoffValueService
        kickoff = instance_template.kickoff_instance
        kickoff_value_slz = KickoffValueSerializer(
            data={
                'account_id': instance_template.account.id,
                'workflow': self.instance.id,
                'kickoff': kickoff.id,
                'description': kickoff.description,
                'fields_data': kwargs.get('kickoff_fields_data', {})
            },
            context={'user': self.user}
        )
        kickoff_value_slz.is_valid(raise_exception=True)
        kickoff_value_slz.save()

        # insert kickoff fields values
        if contains_fields_vars(self.instance.name):
            self.instance.name = insert_kickoff_fields_vars(self.instance)

        # After insert fields vars
        self.instance.name = string_abbreviation(
            name=self.instance.name,
            length=WORKFLOW_NAME_LENGTH
        )
        self.instance.save(update_fields=['name'])
        self.instance.members.add(
            *set(instance_template.template_owners.only_ids())
        )
        return self.instance

    def _create_related(
        self,
        instance_template: Template,
        **kwargs
    ):

        for task_template in instance_template.tasks.order_by('number'):
            task_service = TaskService(user=self.user)
            task_service.create(
                instance_template=task_template,
                workflow=self.instance,
                redefined_performer=kwargs.get('redefined_performer')
            )
        return self.instance

    def _create_actions(self, **kwargs):
        if kwargs.get('anonymous_id'):
            AnalyticService.workflows_started(
                workflow=self.instance,
                auth_type=self.auth_type,
                is_superuser=self.is_superuser,
                anonymous_id=kwargs['anonymous_id']
            )
        else:
            AnalyticService.workflows_started(
                workflow=self.instance,
                auth_type=self.auth_type,
                is_superuser=self.is_superuser,
                user_id=self.user.id
            )
        if self.instance.is_urgent:
            AnalyticService.workflows_urgent(
                workflow=self.instance,
                auth_type=self.auth_type,
                is_superuser=self.is_superuser,
                user_id=self.user.id,
                action=WorkflowActions.marked
            )

        if self.auth_type == AuthTokenType.API:
            service = TemplateIntegrationsService(
                account=self.user.account,
                is_superuser=self.is_superuser,
                user=self.user
            )
            service.api_request(
                template=self.instance.template,
                user_agent=kwargs.get('user_agent')
            )

    def create(
        self,
        **kwargs
    ) -> Workflow:
        super().create(**kwargs)
        send_workflow_started_webhook.delay(
            user_id=self.user.id,
            instance_id=self.instance.id
        )
        return self.instance
