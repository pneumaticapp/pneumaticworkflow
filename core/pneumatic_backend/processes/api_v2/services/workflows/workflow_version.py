from typing import Dict, List, Tuple
from django.contrib.auth import get_user_model
from pneumatic_backend.processes.api_v2.services.base import (
    BaseUpdateVersionService,
)
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
from pneumatic_backend.processes.models import TaskPerformer
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
        self.instance = workflow_service.partial_update(
            current_task=self.instance.tasks_count,
            force_save=True
        )
        action_service = WorkflowActionService(
            user=self.user,
            is_superuser=self.is_superuser,
            auth_type=self.auth_type,
            sync=self.sync
        )
        action_service.end_process(
            workflow=self.instance,
            user=self.user,
            by_condition=False,
            by_complete_task=True
        )

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
            template_id__in={elem['id'] for elem in data}
        ).delete()

    def _get_current_task_from_version(
        self,
        data: List[dict]
    ) -> Tuple[int, bool]:

        # TODO Split to two functions when current task changed and not

        task_template_ids = {elem['id'] for elem in data}
        current_task = self.instance.current_task_instance
        is_deleted_current_task = (
            current_task.template_id not in task_template_ids
        )
        last_template_id = None
        current_template_id = current_task.template_id

        if is_deleted_current_task:
            last_completed = self.instance.tasks.filter(
                template_id__in=task_template_ids
            ).completed().order_by(
                'number'
            ).last()
            last_template_id = (
                last_completed.template_id
                if last_completed else
                None
            )

        template_id = (
            last_template_id if is_deleted_current_task else
            current_template_id
        )

        number = 1
        for task_data in data:
            if template_id == task_data['id']:
                if is_deleted_current_task:
                    number = task_data['number'] + 1
                    break
                number = task_data['number']
                break
        return number, is_deleted_current_task

    def _complete_workflow(self):

        self.complete_up_to_task(self.instance.tasks_count + 1)
        self.instance.current_task = self.instance.tasks_count
        WorkflowActionService().end_process(
            workflow=self.instance,
            user=self.user,
            by_condition=False,
            by_complete_task=True
        )

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
                'template_owners': list,
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
            prev_current_task.taskperformer_set.users().not_completed()
            .exclude_directly_deleted().user_ids_set()
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
        self.instance.members.add(*data['template_owners'])
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
                is_superuser=self.is_superuser,
                auth_type=self.auth_type,
                user=self.user,
                sync=self.sync
            )
            if self.instance.is_delayed:
                if changed:
                    # if current task deleted from template with delay
                    action_service.resume_workflow_with_new_current_task(
                        workflow=self.instance
                    )
                else:
                    delay = current_task.get_active_delay()
                    if not delay or (delay and delay.is_expired):
                        action_service.resume_workflow(workflow=self.instance)
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
                    action_method(
                        workflow=self.instance,
                        task=current_task,
                        user=self.user,
                        by_condition=by_cond,
                    )
                else:
                    if current_task.can_be_completed():
                        first_completed_user = (
                            current_task.taskperformer_set.completed(
                            ).exclude_directly_deleted().first().user
                        )
                        action_service.user = first_completed_user
                        action_service.complete_task(current_task)
                    else:
                        not_completed_ids = (
                            TaskPerformer.objects.by_task(
                                current_task.id
                            ).exclude_directly_deleted().users()
                            .not_completed().user_ids_set()
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
