from typing import Dict, Tuple
from django.utils import timezone
from django.contrib.auth import get_user_model
from pneumatic_backend.processes.models.templates.checklist import (
    ChecklistTemplateSelection
)
from pneumatic_backend.processes.models import (
    ChecklistSelection,
    Task,
)
from pneumatic_backend.processes.api_v2.services.task import exceptions
from pneumatic_backend.processes.api_v2.services.base import (
    BaseWorkflowService,
    BaseUpdateVersionService,
)
from pneumatic_backend.processes.utils.common import (
    insert_fields_values_to_text
)
from pneumatic_backend.processes.enums import WorkflowStatus
from pneumatic_backend.processes.messages.workflow import (
    MSG_PW_0017,
    MSG_PW_0018,
    MSG_PW_0019,
    MSG_PW_0020,
)


UserModel = get_user_model()


class ChecklistSelectionVersionService(BaseUpdateVersionService):

    def update_from_version(
        self,
        data: dict,
        version: int,
        **kwargs
    ) -> Tuple[ChecklistSelection, bool]:

        """
            data = {
                'api_name': str,
                'value': str,
            }
        """

        checklist = kwargs['checklist']
        value = insert_fields_values_to_text(
            fields_values=kwargs['fields_values'],
            text=data['value']
        )
        self.instance, created = ChecklistSelection.objects.update_or_create(
            checklist=checklist,
            api_name=data['api_name'],
            defaults={
                'value': value,
                'value_template': data['value'],
            }
        )
        return self.instance, created


class ChecklistSelectionService(BaseWorkflowService):

    def _create_instance(
        self,
        instance_template: ChecklistTemplateSelection,
        **kwargs
    ):

        self.instance = ChecklistSelection.objects.create(
            api_name=instance_template.api_name,
            checklist=kwargs['checklist'],
            value=instance_template.value,
            value_template=instance_template.value,
        )

    def _create_related(
        self,
        instance_template: ChecklistTemplateSelection,
        **kwargs
    ):
        pass

    def _validate_permission_to_mark(
        self,
        task: Task,
        user: UserModel,
    ):
        performers = task.taskperformer_set.exclude_directly_deleted()
        is_performer = user.id in performers.values_list(
            'user_id', flat=True
        )
        user_permission = user.is_account_owner or is_performer
        if not user_permission:
            raise exceptions.ChecklistServiceException(MSG_PW_0019)
        workflow = task.workflow
        if workflow.status in WorkflowStatus.END_STATUSES:
            raise exceptions.ChecklistServiceException(MSG_PW_0017)
        if workflow.status == WorkflowStatus.DELAYED:
            raise exceptions.ChecklistServiceException(MSG_PW_0020)
        if task.number != workflow.current_task:
            raise exceptions.ChecklistServiceException(MSG_PW_0018)

    def _update_marked_count(self, task: Task):
        task.checklists_marked = ChecklistSelection.objects.filter(
            checklist__task=task,
        ).marked().count()
        task.save()

    def insert_fields_values(
        self,
        fields_values: Dict[str, str],
    ):
        self.instance.value = insert_fields_values_to_text(
            text=self.instance.value_template,
            fields_values=fields_values
        )
        self.update_fields.add('value')

    def mark(self):
        task = self.instance.checklist.task
        self._validate_permission_to_mark(user=self.user, task=task)
        if not self.instance.is_selected:
            self.partial_update(
                date_selected=timezone.now(),
                selected_user_id=self.user.id,
                force_save=True
            )
            self._update_marked_count(task)

    def unmark(self):
        task = self.instance.checklist.task
        self._validate_permission_to_mark(user=self.user, task=task)
        if self.instance.is_selected:
            self.partial_update(
                date_selected=None,
                selected_user_id=self.user.id,
                force_save=True
            )
            self._update_marked_count(task)
