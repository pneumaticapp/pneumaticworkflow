from typing import Dict, List

from django.contrib.auth import get_user_model

from src.notifications.tasks import (
    send_removed_task_notification,
)
from src.processes.models.templates.template import Template
from src.processes.models.workflows.task import Task
from src.processes.services.base import (
    BaseUpdateVersionService,
)
from src.processes.services.tasks.task_version import (
    TaskUpdateVersionService,
)
from src.processes.services.workflow_action import (
    WorkflowActionService,
)
from src.processes.services.workflows.kickoff_version import (
    KickoffUpdateVersionService,
)
from src.processes.services.workflows.workflow import (
    WorkflowService,
)

UserModel = get_user_model()


class WorkflowUpdateVersionService(BaseUpdateVersionService):

    def _before_delete_task_actions(
        self,
        task: Task,
    ):
        recipients = list(
            task
            .taskperformer_set
            .not_completed()
            .exclude_directly_deleted()
            .get_user_emails_and_ids_set(),
        )
        if recipients:
            send_removed_task_notification.delay(
                task_id=task.id,
                task_data=task.get_data_for_list(),
                recipients=recipients,
                account_id=task.account_id,
            )

    def _delete_tasks(self, tasks_api_names: List[str]):
        deleted_tasks = (
            self.instance.tasks
            .apd_status()
            .exclude(api_name__in=tasks_api_names)
            .order_by('id')
        )
        for task in deleted_tasks:
            self._before_delete_task_actions(task)
        deleted_tasks.delete()

    def _update_tasks_from_version(
        self,
        version: int,
        tasks_data: List[Dict],
    ):
        tasks_api_names = []
        task_service = TaskUpdateVersionService(
            user=self.user,
            sync=self.sync,
            auth_type=self.auth_type,
            is_superuser=self.is_superuser,
        )
        for data in tasks_data:
            task_service.update_from_version(
                workflow=self.instance,
                version=version,
                data=data,
            )
            tasks_api_names.append(data['api_name'])
        self._delete_tasks(tasks_api_names=tasks_api_names)

    def update_from_version(
        self,
        data: dict,
        version: int,
        **kwargs,
    ):
        """
            data = {
                'description': str,
                'finalizable': bool,
                'tasks': list,
                'owners': list,
                'kickoff': dict,
            }
        """

        kickoff_service = KickoffUpdateVersionService(
            is_superuser=self.is_superuser,
            auth_type=self.auth_type,
            user=self.user,
            instance=self.instance.kickoff_instance,
        )
        kickoff_service.update_from_version(
            data=data['kickoff'],
            version=version,
        )
        workflow_service = WorkflowService(
            instance=self.instance,
            user=self.user,
            is_superuser=self.is_superuser,
            auth_type=self.auth_type,
        )
        self.instance = workflow_service.partial_update(
            description=data['description'],
            finalizable=data['finalizable'],
            reminder_notification=data['reminder_notification'],
            completion_notification=data['completion_notification'],
            version=version,
            force_save=True,
        )
        template_owners_ids = Template.objects.filter(
            id=data['id'],
        ).get_owners_as_users()
        self.instance.owners.set(template_owners_ids)
        self.instance.members.add(*template_owners_ids)
        self._update_tasks_from_version(
            tasks_data=data['tasks'],
            version=version,
        )
        action_service = WorkflowActionService(
            workflow=self.instance,
            user=self.user,
            is_superuser=self.is_superuser,
            auth_type=self.auth_type,
            sync=self.sync,
        )
        action_service.update_tasks_status()
