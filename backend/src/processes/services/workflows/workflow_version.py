from typing import Dict, List

from django.contrib.auth import get_user_model

from src.notifications.tasks import (
    send_removed_task_deleted_notification,
)
from src.processes.models.templates.template import Template
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

    def _update_tasks_from_version(
        self,
        version: int,
        tasks_data: List[Dict],
    ):
        tasks_api_names = []
        for data in tasks_data:
            task_service = TaskUpdateVersionService(
                user=self.user,
                sync=self.sync,
                auth_type=self.auth_type,
                is_superuser=self.is_superuser,
            )
            task_service.update_from_version(
                workflow=self.instance,
                version=version,
                data=data,
            )
            tasks_api_names.append(data['api_name'])
        deleted_tasks = self.instance.tasks.exclude(
            api_name__in=tasks_api_names,
        )
        for deleted_task in deleted_tasks:
            recipients = list(
                deleted_task
                .taskperformer_set
                .not_completed()
                .exclude_directly_deleted()
                .get_user_emails_and_ids_set(),
            )
            send_removed_task_deleted_notification.delay(
                task_id=deleted_task.id,
                task_data=deleted_task.get_data_for_list(),
                recipients=recipients,
                account_id=deleted_task.account_id,
            )

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
