from typing import Optional, Dict, Any
from django.contrib.auth import get_user_model
from pneumatic_backend.processes.consts import WORKFLOW_NAME_LENGTH
from pneumatic_backend.processes.utils.common import (
    string_abbreviation,
)
from pneumatic_backend.processes.serializers.kickoff_value import (
    KickoffValueSerializer
)
from pneumatic_backend.processes.api_v2.services.task.task import TaskService


UserModel = get_user_model()


class WorkflowSerializerMixin:

    def _update_tasks(
        self,
        update_fields_values: bool,
        is_urgent: Optional[bool] = None,
    ):
        tasks = self.instance.tasks.filter(
            number__lte=self.instance.current_task
        ).order_by('number')
        if is_urgent is not None and not update_fields_values:
            tasks.update(is_urgent=is_urgent)
        elif update_fields_values:
            fields_values = self.instance.get_fields_markdown_values(
                tasks_filter_kwargs={'number__lt': self.instance.current_task},
            )
            for task in tasks:
                task_service = TaskService(
                    instance=task,
                    user=self.context['user']
                )
                if is_urgent is not None:
                    task_service.partial_update(is_urgent=is_urgent)
                task_service.insert_fields_values(fields_values)
                if task.number == self.instance.current_task:
                    task_service.set_due_date_from_template()
                    task.update_performers()

    def _update_kickoff_value(
        self,
        fields_data: Dict[str, Any]
    ):
        kickoff_slz = KickoffValueSerializer(
            data={
                'fields_data': fields_data
            },
            instance=self.instance.kickoff_instance,
            partial=True,
            context={
                'user': self.context['user']
            }
        )
        kickoff_slz.is_valid(raise_exception=True)
        return kickoff_slz.save()

    def _partial_update_workflow(self, **kwargs):
        update_fields = []
        if 'name' in kwargs:
            self.instance.name = string_abbreviation(
                name=kwargs['name'],
                length=WORKFLOW_NAME_LENGTH
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
