from typing import Dict, List, Tuple
from django.contrib.auth import get_user_model
from pneumatic_backend.processes.api_v2.services.base import (
    BaseUpdateVersionService,
)
from pneumatic_backend.processes.enums import PerformerType
from pneumatic_backend.processes.api_v2.services.task.task_version import (
    TaskUpdateVersionService,
)
from pneumatic_backend.processes.api_v2.services.workflows.\
    kickoff_version import (
        KickoffUpdateVersionService
    )
from pneumatic_backend.processes.api_v2.services.workflows.workflow import (
    WorkflowService
)
from pneumatic_backend.processes.models import (
    TaskPerformer,
    Template
)
from pneumatic_backend.processes.services.workflow_action import (
    WorkflowActionService,
)
from pneumatic_backend.processes.services.websocket import WSSender


UserModel = get_user_model()


class WorkflowUpdateVersionService(BaseUpdateVersionService):

    def _end_workflow(self):

        workflow_service = WorkflowService(
            instance=self.instance,
            user=self.user,
            is_superuser=self.is_superuser,
            auth_type=self.auth_type
        )
        active_tasks_count = self.instance.tasks.filter(
            status=False
        ).count()
        active_current_task = (
            self.instance.tasks_count - (
                self.instance.tasks_count - active_tasks_count
            )
        )
        if active_current_task < 1:
            active_current_task = 1
        self.instance = workflow_service.partial_update(
            current_task=self.instance.tasks_count,
            active_tasks_count=active_tasks_count,
            active_current_task=active_current_task,
            force_save=True
        )
        action_service = WorkflowActionService(
            workflow=self.instance,
            user=self.user,
            is_superuser=self.is_superuser,
            auth_type=self.auth_type,
            sync=self.sync
        )
        action_service.end_process(by_condition=False, by_complete_task=True)

    def _update_tasks_from_version(
        self,
        version: int,
        data: List[Dict],
    ):
        for task_data in sorted(data, key=lambda x: x['number']):
            task_service = TaskUpdateVersionService(
                user=self.user,
                sync=self.sync,
                auth_type=self.auth_type,
                is_superuser=self.is_superuser
            )
            task_service.update_from_version(
                workflow=self.instance,
                version=version,
                data=task_data
            )
        self.instance.tasks.exclude(
            api_name__in={elem['api_name'] for elem in data}
        ).delete()

    def _get_current_task_from_version(
        self,
        data: List[dict]
    ) -> Tuple[int, bool]:

        # TODO Split to two functions when current task changed and not

        task_template_api_names = {elem['api_name'] for elem in data}
        current_task = self.instance.current_task_instance
        is_deleted_current_task = (
            current_task.api_name not in task_template_api_names
        )
        last_template_api_name = None
        current_template_api_name = current_task.api_name

        if is_deleted_current_task:
            last_completed = self.instance.tasks.filter(
                api_name__in=task_template_api_names
            ).completed().order_by(
                'number'
            ).last()
            last_template_api_name = (
                last_completed.api_name
                if last_completed else
                None
            )

        template_api_name = (
            last_template_api_name if is_deleted_current_task else
            current_template_api_name
        )

        number = 1
        for task_data in data:
            if template_api_name == task_data['api_name']:
                if is_deleted_current_task:
                    number = task_data['number'] + 1
                    break
                number = task_data['number']
                break
        return number, is_deleted_current_task

    def _complete_workflow(self):

        self.complete_up_to_task(self.instance.tasks_count + 1)
        self.instance.current_task = self.instance.tasks_count
        service = WorkflowActionService(
            workflow=self.instance,
            user=self.user,
            is_superuser=self.is_superuser,
            auth_type=self.auth_type,
            sync=self.sync
        )
        service.end_process(by_condition=False, by_complete_task=True)

    def update_from_version(
        self,
        data: dict,
        version: int,
        **kwargs
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
            instance=self.instance.kickoff_instance
        )
        kickoff_service.update_from_version(
            data=data['kickoff'],
            version=version
        )
        current_task, changed = self._get_current_task_from_version(
            data['tasks']
        )
        prev_current_task = self.instance.current_task_instance
        prev_not_completed_ids = (
            prev_current_task
            .taskperformer_set
            .not_completed()
            .exclude_directly_deleted()
            .get_user_ids_set()
        )
        workflow_service = WorkflowService(
            instance=self.instance,
            user=self.user,
            is_superuser=self.is_superuser,
            auth_type=self.auth_type
        )

        self.instance = workflow_service.partial_update(
            description=data['description'],
            finalizable=data['finalizable'],
            tasks_count=len(data['tasks']),
            current_task=current_task,
            version=version,
            force_save=True
        )
        tempalate_owners_ids = Template.objects.filter(
            id=data['id']
        ).get_owners_as_users()
        self.instance.owners.set(tempalate_owners_ids)
        self.instance.members.add(*tempalate_owners_ids)
        self._update_tasks_from_version(
            data=data['tasks'],
            version=version
        )

        # Workflow actions
        if self.instance.current_task > self.instance.tasks_count:
            self._end_workflow()
        else:
            current_task = self.instance.current_task_instance
            self.instance.members.add(
                *current_task.performers.exclude_directly_deleted().only_ids()
            )
            action_service = WorkflowActionService(
                workflow=self.instance,
                is_superuser=self.is_superuser,
                auth_type=self.auth_type,
                user=self.user,
                sync=self.sync
            )
            if self.instance.is_delayed:
                if changed:
                    # if current task deleted from template with delay
                    action_service.resume_workflow_with_new_current_task()
                else:
                    delay = current_task.get_active_delay()
                    if not delay or (delay and delay.is_expired):
                        action_service.resume_workflow()
            else:
                if changed:
                    # if current task deleted from template
                    WSSender.send_removed_task_notification(
                        task=prev_current_task,
                        user_ids=prev_not_completed_ids,
                        sync=self.sync
                    )
                    action_method, by_cond = action_service.execute_condition(
                        current_task
                    )
                    action_method(task=current_task, by_condition=by_cond)
                else:
                    if current_task.can_be_completed():
                        first_completed_user = (
                            current_task.taskperformer_set.completed()
                            .exclude_directly_deleted()
                            .exclude(type=PerformerType.GROUP)
                            .first()
                            .user
                        )
                        if first_completed_user is None:
                            group = (
                                current_task.taskperformer_set.completed()
                                .exclude_directly_deleted()
                                .filter(type=PerformerType.GROUP)
                                .first()
                                .group
                            )
                            first_completed_user = group.users.first().user
                        action_service.user = first_completed_user
                        action_service.complete_task(current_task)
                    else:
                        not_completed_ids = (
                            TaskPerformer.objects
                            .by_task(current_task.id)
                            .exclude_directly_deleted()
                            .not_completed()
                            .get_user_ids_set()
                        )
                        new_performers_ids = (
                            not_completed_ids - prev_not_completed_ids
                        )
                        deleted_performers_ids = (
                            prev_not_completed_ids - not_completed_ids
                        )
                        if new_performers_ids:
                            WSSender.send_new_task_notification(
                                task=current_task,
                                user_ids=new_performers_ids,
                                sync=self.sync
                            )
                        if deleted_performers_ids:
                            WSSender.send_removed_task_notification(
                                task=current_task,
                                user_ids=deleted_performers_ids,
                                sync=self.sync
                            )
