from datetime import datetime
from typing import Callable, Iterable, Optional, Tuple

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from src.analysis.services import AnalyticService
from src.authentication.enums import AuthTokenType
from src.authentication.services.guest_auth import GuestJWTAuthService
from src.notifications.tasks import (
    send_complete_task_notification,
    send_delayed_workflow_notification,
    send_new_task_notification,
    send_new_task_websocket,
    send_removed_task_notification,
    send_resumed_workflow_notification,
)
from src.processes.enums import (
    ConditionAction,
    DirectlyStatus,
    TaskStatus,
    WorkflowStatus,
)
from src.processes.messages import workflow as messages
from src.processes.models.workflows.task import (
    Delay,
    Task,
    TaskPerformer,
)
from src.processes.models.workflows.workflow import Workflow
from src.processes.services import exceptions
from src.processes.services.condition_check.service import (
    ConditionCheckService,
)
from src.processes.services.events import (
    WorkflowEventService,
)
from src.processes.services.tasks.field import (
    TaskFieldService,
)
from src.processes.services.tasks.task import TaskService
from src.processes.tasks.webhooks import (
    send_task_completed_webhook,
    send_task_returned_webhook,
    send_workflow_completed_webhook,
    send_workflow_started_webhook,
)
from src.services.markdown import MarkdownService
from src.webhooks.models import WebHook

UserModel = get_user_model()


class WorkflowActionService:

    def __init__(
        self,
        user: UserModel,
        workflow: Workflow,
        is_superuser: bool = False,
        auth_type: AuthTokenType.LITERALS = AuthTokenType.USER,
        sync: bool = False,
    ):
        self.workflow = workflow
        if user is None:
            raise Exception(
                'Specify user before initialization WorkflowActionService',
            )
        self.user = user
        self.account = user.account
        self.is_superuser = is_superuser
        self.auth_type = auth_type
        self.sync = sync

    def check_delay_workflow(self):

        if (
            self.workflow.is_running
            and self.workflow.tasks.active().count() == 0
            and self.workflow.tasks.delayed().count() > 0
        ):
            self.workflow.status = WorkflowStatus.DELAYED
            self.workflow.save(update_fields=['status'])

    def force_delay_workflow(self, date: datetime):

        """ Create or update existent task delay with new duration """

        with transaction.atomic():
            self.workflow.status = WorkflowStatus.DELAYED
            self.workflow.save(update_fields=['status'])
            now = timezone.now()
            duration = date - now
            delay = None  # Crutch
            for task in self.workflow.tasks.active():
                task.status = TaskStatus.DELAYED
                task.save(update_fields=['status'])
                delay = task.get_active_delay()

                if delay:
                    delay.directly_status = DirectlyStatus.CREATED
                    delay.duration = duration
                    delay.start_date = now
                    delay.save(
                        update_fields=[
                            'duration',
                            'start_date',
                            'directly_status',
                        ],
                    )
                else:
                    delay = Delay.objects.create(
                        task=task,
                        duration=duration,
                        start_date=now,
                        directly_status=DirectlyStatus.CREATED,
                        workflow=self.workflow,
                    )
                recipients = list(
                    TaskPerformer.objects
                    .filter(task_id=task.id)
                    .exclude_directly_deleted()
                    .not_completed()
                    .get_user_emails_and_ids_set(),
                )
                # notifications about event
                for (user_id, user_email) in recipients:
                    send_delayed_workflow_notification.delay(
                        logging=self.account.log_api_requests,
                        logo_lg=self.account.logo_lg,
                        author_id=self.user.id,
                        user_id=user_id,
                        user_email=user_email,
                        account_id=self.account.id,
                        task_id=task.id,
                    )
                send_removed_task_notification.delay(
                    account_id=self.account.id,
                    task_id=task.id,
                    recipients=recipients,
                )
            WorkflowEventService.force_delay_workflow_event(
                workflow=self.workflow,
                user=self.user,
                delay=delay,
            )

            AnalyticService.workflow_delayed(
                user=self.user,
                workflow=self.workflow,
                is_superuser=self.is_superuser,
                auth_type=self.auth_type,
                duration=duration,
            )

    def resume_task(self, task: Task):

        if self.workflow.is_completed:
            raise exceptions.ResumeCompletedWorkflow

        with transaction.atomic():
            self.continue_task(task)
            if not self.workflow.tasks.delayed().exists():
                self.workflow.status = WorkflowStatus.RUNNING
                self.workflow.save(update_fields=['status'])

    def force_resume_workflow(self):

        """ Resume delayed workflow before the timeout """

        if self.workflow.is_running:
            return
        if self.workflow.is_completed:
            raise exceptions.ResumeCompletedWorkflow

        with transaction.atomic():
            self.workflow.status = WorkflowStatus.RUNNING
            self.workflow.save(update_fields=['status'])
            WorkflowEventService.force_resume_workflow_event(
                workflow=self.workflow,
                user=self.user,
            )
            for task in self.workflow.tasks.delayed():
                send_resumed_workflow_notification.delay(
                    logging=self.account.log_api_requests,
                    logo_lg=self.account.logo_lg,
                    author_id=self.user.id,
                    account_id=self.account.id,
                    task_id=task.id,
                )
                self.continue_task(task)

    def terminate_workflow(self):

        for task in self.workflow.tasks.active():
            recipients = list(
                TaskPerformer.objects.filter(task_id=task.id)
                .exclude_directly_deleted()
                .not_completed()
                .get_user_emails_and_ids_set(),
            )
            send_removed_task_notification.delay(
                task_id=task.id,
                task_data=task.get_data_for_list(),
                recipients=recipients,
                account_id=task.account_id,
            )
        for task_id in self.workflow.tasks.only_ids():
            GuestJWTAuthService.deactivate_task_guest_cache(
                task_id=task_id,
            )
        AnalyticService.workflows_terminated(
            user=self.user,
            workflow=self.workflow,
            is_superuser=self.is_superuser,
            auth_type=self.auth_type,
        )
        self.workflow.delete()

    def _complete_workflow(self):

        for task in self.workflow.tasks.delayed():
            delay = task.get_active_delay()
            delay.end_date = timezone.now()
            delay.save(update_fields=['end_date'])
            task.status = TaskStatus.ACTIVE
            task.save(update_fields=['status'])

        tasks_ids = self.workflow.tasks.only_ids()
        for task_id in tasks_ids:
            GuestJWTAuthService.deactivate_task_guest_cache(
                task_id=task_id,
            )

        update_fields = ['status', 'date_completed']
        if self.workflow.is_urgent:
            self.workflow.is_urgent = False
            update_fields.append('is_urgent')
            Task.objects.filter(id__in=tasks_ids).update(is_urgent=False)
        self.workflow.status = WorkflowStatus.DONE
        self.workflow.date_completed = timezone.now()
        self.workflow.save(update_fields=update_fields)
        if WebHook.objects.on_account(self.account.id).wf_completed().exists():
            send_workflow_completed_webhook.delay(
                user_id=self.user.id,
                account_id=self.account.id,
                payload=self.workflow.webhook_payload(),
            )

    def force_complete_workflow(self):

        self._complete_workflow()
        WorkflowEventService.workflow_ended_event(
            workflow=self.workflow,
            user=self.user,
        )
        for task in self.workflow.tasks.active():
            recipients = list(
                TaskPerformer.objects.filter(task=task)
                .exclude_directly_deleted()
                .not_completed()
                .get_user_emails_and_ids_set(),
            )
            send_removed_task_notification.delay(
                task_id=task.id,
                recipients=recipients,
                account_id=task.account_id,
            )

    def end_process(
        self,
        task: Task,
        by_condition: bool = False,
        by_complete_task: bool = False,
        **kwargs,
    ):
        if by_condition:
            self._complete_workflow()
            WorkflowEventService.workflow_ended_by_condition_event(
                workflow=self.workflow,
                task=task,
                user=self.user,
            )
        elif by_complete_task:
            self._complete_workflow()
            WorkflowEventService.workflow_complete_event(
                workflow=self.workflow,
                task=task,
                user=self.user,
            )
            AnalyticService.workflow_completed(
                user=self.user,
                is_superuser=self.is_superuser,
                auth_type=self.auth_type,
                workflow=self.workflow,
            )
        else:
            self.force_complete_workflow()

    def skip_task(
        self,
        task: Task,
        is_returned: bool = False,
        **kwargs,
    ):
        task_service = TaskService(
            instance=task,
            user=self.user or self.workflow.account.get_owner(),
        )
        fields_values = self.workflow.get_fields_markdown_values(
            tasks_filter_kwargs={'task__status__in': (
                TaskStatus.COMPLETED, TaskStatus.SKIPPED,
            )},
        )
        task_service.insert_fields_values(fields_values=fields_values)

        WorkflowEventService.task_skip_event(task)
        if is_returned and task.parents:
            task.status = TaskStatus.PENDING
            task.save(update_fields=['status'])
            self._start_prev_tasks(task)
        else:
            task.status = TaskStatus.SKIPPED
            task.save(update_fields=['status'])
            self._start_next_tasks(parent_task=task)

    def _execute_skip_conditions(
        self,
        task: Task,
    ) -> Optional[Callable]:

        skip_task_condition_passed = False
        for condition in task.conditions.skip_task():
            condition_passed = ConditionCheckService.check(
                condition=condition,
                workflow_id=task.workflow_id,
            )
            if condition_passed:
                if condition.action == ConditionAction.END_WORKFLOW:
                    return self.end_process
                if condition.action == ConditionAction.SKIP_TASK:
                    skip_task_condition_passed = True
        if skip_task_condition_passed:
            return self.skip_task
        return None

    def execute_conditions(
        self,
        task: Task,
    ) -> Tuple[Optional[Callable], bool]:

        """ Return pair:
            - method : condition action
            - marker, that indicates if method selected by condition

            Returns the action with the highest priority. Priority order:
                1. End workflow
                2. Skip task
                3. Start task
        """

        start_condition_passed = False
        start_condition_exists = False
        for condition in task.conditions.start_task():
            start_condition_passed = ConditionCheckService.check(
                condition=condition,
                workflow_id=task.workflow_id,
            )
            start_condition_exists = True

        if not start_condition_exists:
            # If there is no start condition,
            # the task is started immediately
            # - check skip conditions before start.
            skip_action = self._execute_skip_conditions(task)
            if skip_action:
                return skip_action, True
            return self.start_task, False
        if start_condition_passed:
            # Start task condition passed
            # - check skip conditions before start
            skip_action = self._execute_skip_conditions(task)
            if skip_action:
                return skip_action, True
            return self.start_task, False
        # Start task condition not passed - task continues to wait
        return None, False

    def start_workflow(self):

        # Duplicate start task code, need for workflow_run_event
        tasks = self.workflow.tasks.filter(parents=[])
        for task in tasks:
            task_service = TaskService(instance=task, user=self.user)
            fields_values = self.workflow.get_kickoff_fields_markdown_values()
            task_service.insert_fields_values(fields_values=fields_values)

        WorkflowEventService.workflow_run_event(
            workflow=self.workflow,
            user=self.user,
        )
        if self.workflow.ancestor_task:
            WorkflowEventService.sub_workflow_run_event(
                workflow=self.workflow.ancestor_task.workflow,
                sub_workflow=self.workflow,
                user=self.user,
            )
        self._start_next_tasks()
        self.check_delay_workflow()
        if WebHook.objects.on_account(
            self.account.id,
        ).wf_started().exists():
            send_workflow_started_webhook.delay(
                user_id=self.user.id,
                account_id=self.account.id,
                payload=self.workflow.webhook_payload(),
            )

    def continue_workflow(self, task: Task, is_returned: bool = False):
        if not self.workflow.is_running:
            self.workflow.status = WorkflowStatus.RUNNING
            self.workflow.save(update_fields=['status'])
        users_performers_set = (
            TaskPerformer.objects
            .exclude_directly_deleted()
            .by_task(task.id)
            .get_user_ids_set()
        )
        self.workflow.members.add(*users_performers_set)
        self.continue_task(task=task, is_returned=is_returned)

    def continue_task(self, task: Task, is_returned: bool = False):

        """ Continue start task after run or workflow delay """

        task_start_event_already_exist = (
            not is_returned and bool(task.date_started)
        )
        delay = task.get_active_delay()
        if delay:
            delay.end_date = timezone.now()
            delay.save(update_fields=['end_date'])
        task_service = TaskService(
            instance=task,
            user=self.user,
        )
        task_service.partial_update(
            is_urgent=self.workflow.is_urgent,
            date_completed=None,
            status=TaskStatus.ACTIVE,
            date_started=timezone.now(),
            force_save=True,
        )
        task_service.set_due_date_from_template()
        (
            TaskPerformer.objects
            .by_workflow(self.workflow.id).with_tasks_after(task)
            .update(is_completed=False, date_completed=None)
        )
        # if task force snoozed then start task event already exists
        # but if task returned then
        if not task_start_event_already_exist:
            WorkflowEventService.task_started_event(task)

        if not self.workflow.template.is_onboarding:
            recipients_qst = (
                TaskPerformer.objects
                .by_task(task.id)
                .exclude_directly_deleted()
                .new_task_recipients()
            ).order_by('id')

            wf_starter = self.workflow.workflow_starter
            ws_recipients = None
            recipients = []
            # Sent only websocket
            # to the workflow starter performer on first tasks
            if (
                len(task.parents) == 0
                and not is_returned
                and not self.workflow.is_external
            ):
                for el in recipients_qst:
                    if el.user_id == wf_starter.id:
                        ws_recipients = (
                            (el.user_id, el.email, el.is_subscribed),
                        )
                    else:
                        recipients.append(
                            (el.user_id, el.email, el.is_subscribed),
                        )
            else:
                recipients = [
                    (el.user_id, el.email, el.is_subscribed)
                    for el in recipients_qst
                ]
            task_data = None
            if recipients:
                task_data = task.get_data_for_list()
                send_new_task_notification.delay(
                    logging=self.account.log_api_requests,
                    account_id=self.account.id,
                    recipients=recipients,
                    task_id=task.id,
                    task_name=task.name,
                    task_data=task_data,
                    task_description=task.description,
                    workflow_name=self.workflow.name,
                    template_name=self.workflow.get_template_name(),
                    workflow_starter_name=(
                        None if self.workflow.is_external else wf_starter.name
                    ),
                    workflow_starter_photo=(
                        None if self.workflow.is_external else wf_starter.photo
                    ),
                    due_date_timestamp=(
                        task.due_date.timestamp() if task.due_date else None
                    ),
                    logo_lg=task.account.logo_lg,
                    is_returned=is_returned,
                )
            if ws_recipients:
                send_new_task_websocket.delay(
                    logging=self.account.log_api_requests,
                    task_id=task.id,
                    recipients=ws_recipients,
                    account_id=self.account.id,
                    task_data=task_data or task.get_data_for_list(),
                )

        for task_id in self.workflow.tasks.filter(
            parents__contains=[task.api_name],
        ).only_ids():
            GuestJWTAuthService.delete_task_guest_cache(
                task_id=task_id,
            )
        self._start_next_tasks()

    def _start_prev_tasks(
        self,
        child_task: Task,
    ):

        for task in Task.objects.filter(
            api_name__in=child_task.parents,
            workflow_id=self.workflow.id,
        ):
            action_method, _ = self.execute_conditions(task)
            if action_method:
                action_method(
                    task=task,
                    is_returned=True,
                )

    def _start_next_tasks(
        self,
        parent_task: Optional[Task] = None,
    ):
        by_complete_task = parent_task and parent_task.is_completed
        if self.workflow.tasks.pending().exists():
            for task in self.workflow.tasks.pending():
                action_method, by_condition = self.execute_conditions(task)
                if action_method:
                    action_method(
                        task=task,
                        by_condition=by_condition,
                        by_complete_task=by_complete_task,
                    )
                    # Since the task status has changed,
                    # the next task in the cycle may have an outdated status.
                    # Next tasks runs in action_method
                    break
        else:  # noqa: PLR5501
            if not self.workflow.tasks.apd_status().exists():
                self.end_process(
                    task=parent_task,
                    by_complete_task=by_complete_task,
                )

    def update_tasks_status(self):
        for task in self.workflow.tasks.apd_status():
            action_method, _ = self.execute_conditions(task)
            if action_method is not None:
                if task.is_pending:
                    action_method(task=task)
                elif task.is_active or task.is_delayed:
                    if action_method.__name__ == ConditionAction.START_TASK:
                        if task.is_delayed:
                            delay = task.get_active_delay()
                            if not delay or (delay and delay.is_expired):
                                self.resume_task(task)
                        if task.can_be_completed():
                            self.complete_task(task=task)
                    else:
                        action_method(task=task)

        if not self.workflow.tasks.apd_status().exists():
            self._complete_workflow()

    def delay_task(self, task: Task, delay: Delay):

        task.status = TaskStatus.DELAYED
        task.save(update_fields=['status'])
        delay.start_date = timezone.now()
        delay.save(update_fields=['start_date'])
        WorkflowEventService.task_delay_event(
            user=self.user,
            task=task,
            delay=delay,
        )

    def start_task(
        self,
        task: Task,
        is_returned: bool = False,
        **kwargs,
    ):

        task_service = TaskService(
            instance=task,
            user=self.user or self.workflow.account.get_owner(),
        )
        fields_values = self.workflow.get_fields_markdown_values(
            tasks_filter_kwargs={'task__status__in': (
                TaskStatus.COMPLETED, TaskStatus.SKIPPED,
            )},
        )
        task_service.insert_fields_values(fields_values=fields_values)
        task.update_performers(restore_performers=True)
        task_performers_exists = (
            TaskPerformer.objects.exclude_directly_deleted().by_task(
                task.id,
            ).exists()
        )
        if not task_performers_exists:
            WorkflowEventService.task_skip_no_performers_event(task)
            task.status = TaskStatus.SKIPPED
            task.save(update_fields=('status',))
            if is_returned:
                self._start_prev_tasks(task)
            else:
                self._start_next_tasks(parent_task=task)
        else:  # noqa: PLR5501
            if is_returned:
                self.continue_workflow(task=task, is_returned=is_returned)
            else:
                delay = task.get_active_delay()
                if delay:
                    self.delay_task(task=task, delay=delay)
                    self._start_next_tasks()
                else:
                    self.continue_workflow(task=task, is_returned=is_returned)

    def complete_task(self, task: Task, by_user: bool = False):

        """ Complete workflow task if it <= current task
            Only for current task run complete actions """

        current_date = timezone.now()
        update_fields = {
            'status': TaskStatus.COMPLETED,
            'date_completed': current_date,
            'date_started': task.date_started or current_date,
        }
        task_service = TaskService(
            instance=task,
            is_superuser=self.is_superuser,
            auth_type=self.auth_type,
            user=self.user,
        )
        task_service.partial_update(**update_fields, force_save=True)
        # Not include guests
        performers_ids = (
            TaskPerformer.objects.by_task(task.id)
            .exclude_directly_deleted()
            .not_completed()
            .users()
            .values_list('id', flat=True)
        )
        recipients = (
            UserModel.objects
            .get_users_in_performer(performers_ids=performers_ids)
            .order_by('id')
            .user_ids_emails_list()
        )
        send_removed_task_notification.delay(
            task_id=task.id,
            recipients=recipients,
            account_id=task.account_id,
        )
        notification_recipients = (
            UserModel.objects
            .get_users_in_performer(performers_ids=performers_ids)
            .filter(is_complete_tasks_subscriber=True)
            .exclude(id=self.user.id)
            .order_by('id')
            .user_ids_emails_list()
        )
        if notification_recipients:
            send_complete_task_notification.delay(
                logging=self.account.log_api_requests,
                author_id=self.user.id,
                account_id=task.account_id,
                recipients=notification_recipients,
                task_id=task.id,
                logo_lg=task.account.logo_lg,
            )
        (
            TaskPerformer.objects
            .by_task(task.id)
            .exclude_directly_deleted()
            .not_completed()
            .update(
                date_completed=timezone.now(),
                is_completed=True,
            )
        )
        if by_user:
            AnalyticService.task_completed(
                user=self.user,
                is_superuser=self.is_superuser,
                auth_type=self.auth_type,
                workflow=self.workflow,
                task=task,
            )
            # Need run after save completed task (and performers)
            # and before start next tasks
            WorkflowEventService.task_complete_event(
                task=task,
                user=self.user,
            )
        self._start_next_tasks(parent_task=task)
        if (
            WebHook.objects
            .on_account(self.account.id)
            .task_completed().exists()
        ):
            send_task_completed_webhook.delay(
                user_id=self.user.id,
                account_id=self.account.id,
                payload=task.webhook_payload(),
            )

    def _task_can_be_completed(self, task: Task) -> bool:

        """ Implies that the specified user has completed the task """

        if task.is_completed is True:
            return False
        task_performers = (
            task.taskperformer_set.exclude_directly_deleted()
        )
        completed_performers = task_performers.filter(
            Q(is_completed=True)
            | Q(is_completed=False, user_id=self.user.id)
            | Q(is_completed=False, group__users=self.user.id),
        ).exists()
        incompleted_performers = task_performers.not_completed().exclude(
            Q(user_id=self.user.id)
            | Q(is_completed=False, group__users=self.user.id),
        ).exists()
        by_all = task.require_completion_by_all
        return (
            (not by_all and completed_performers) or
            (by_all and not incompleted_performers)
        )

    def complete_task_for_user(
        self,
        task: Task,
        fields_values: Optional[dict] = None,
    ):
        if self.workflow.is_delayed:
            raise exceptions.CompleteDelayedWorkflow
        if self.workflow.is_completed:
            raise exceptions.CompleteCompletedWorkflow
        if not task.is_active:
            raise exceptions.CompleteInactiveTask

        task_performer = (
            TaskPerformer.objects
            .by_task(task.id)
            .by_user_or_group(self.user.id)
            .exclude_directly_deleted()
            .first()
        )
        if task_performer:
            if task_performer.is_completed:
                raise exceptions.UserAlreadyCompleteTask
        elif not self.user.is_account_owner:
            raise exceptions.UserNotPerformer

        if not task.checklists_completed:
            raise exceptions.ChecklistIncompleted
        if task.sub_workflows.running().exists():
            raise exceptions.SubWorkflowsIncompleted

        fields_values = fields_values or {}
        with transaction.atomic():
            for task_field in task.output.all():
                service = TaskFieldService(
                    user=self.user,
                    instance=task_field,
                )
                service.partial_update(
                    value=fields_values.get(task_field.api_name),
                    force_save=True,
                )
            if task_performer:
                if self._task_can_be_completed(task):
                    self.complete_task(task=task, by_user=True)
                else:
                    # completed only for user and send ws remove task
                    # if "requires completion by all", sending message
                    # about the completion of the task by each performer
                    task_performer.date_completed = timezone.now()
                    task_performer.is_completed = True
                    task_performer.save(
                        update_fields=('date_completed', 'is_completed'),
                    )
                    if not self.user.is_guest:
                        # Websocket notification
                        send_removed_task_notification.delay(
                            task_id=task.id,
                            recipients=[(self.user.id, self.user.email)],
                            account_id=task.account_id,
                        )
            elif self.user.is_account_owner:
                # account owner force completion
                # not complete performers, but send ws remove task
                self.complete_task(task=task, by_user=True)
        return task

    def _get_not_skipped_revert_task(self, task: Task) -> Optional[Task]:

        action_method, _ = self.execute_conditions(task)
        if action_method and action_method.__name__ in (
            ConditionAction.START_TASK,
            ConditionAction.END_WORKFLOW,
        ):
            return task

        revert_to_tasks = task.get_revert_tasks()
        if not revert_to_tasks:
            return None
        for revert_to_task in revert_to_tasks:
            if self._get_not_skipped_revert_task(revert_to_task) is not None:
                return revert_to_task
        return None

    def _revert_is_possible(
        self,
        revert_to_tasks: Iterable[Task],
    ) -> bool:

        for revert_to_task in revert_to_tasks:
            action_method, _ = self.execute_conditions(revert_to_task)
            if action_method and action_method.__name__ in (
                ConditionAction.START_TASK,
                ConditionAction.END_WORKFLOW,
            ):
                return True

            prev_revert_to_tasks = revert_to_task.get_revert_tasks()
            revert_is_possible = self._revert_is_possible(prev_revert_to_tasks)
            if revert_is_possible:
                return True

        return False

    def _validate_revert_is_possible(
        self,
        revert_to_tasks: Iterable[Task],
    ):

        if not revert_to_tasks:
            raise exceptions.FirstTaskCannotBeReverted

        next_depth_revert_tasks_exists = False
        for revert_to_task in revert_to_tasks:
            action_method, _ = self.execute_conditions(revert_to_task)
            if action_method and action_method.__name__ in (
                ConditionAction.START_TASK,
                ConditionAction.END_WORKFLOW,
            ):
                return True

            next_depth_revert_to_tasks = revert_to_task.get_revert_tasks()
            if next_depth_revert_to_tasks:
                next_depth_revert_tasks_exists = True
                revert_is_possible = self._revert_is_possible(
                    next_depth_revert_to_tasks,
                )
                if revert_is_possible:
                    return True

        if next_depth_revert_tasks_exists:
            raise exceptions.RevertToSkippedTask(
                messages.MSG_PW_0080(revert_to_tasks[0].name),
            )
        raise exceptions.RevertToSkippedTask(
            messages.MSG_PW_0079(revert_to_tasks[0].name),
        )

    def _deactivate_task(self, parent_task: Task):

        dependent_tasks = Task.objects.filter(
            workflow=self.workflow,
            parents__contains=[parent_task.api_name],
        ).exclude(status=TaskStatus.PENDING)
        deactivated_tasks = []
        for task in dependent_tasks:
            action_method, _ = self.execute_conditions(task)
            if action_method is None:
                # Start task condition not completed
                if task.is_delayed:
                    delay = task.get_active_delay()
                    if delay:
                        if delay.directly_status:
                            delay.end_date = timezone.now()
                            delay.save(update_fields=['end_date'])
                        else:
                            task.reset_delay(delay)
                else:
                    # Reset delay from template
                    task.delay_set.filter(
                        directly_status=DirectlyStatus.NO_STATUS,
                    ).update(
                        start_date=None,
                        end_date=None,
                        estimated_end_date=None,
                    )
                if task.is_active:
                    recipients = list(
                        TaskPerformer.objects
                        .filter(task_id=task.id)
                        .exclude_directly_deleted()
                        .not_completed()
                        .get_user_emails_and_ids_set(),
                    )
                    send_removed_task_notification.delay(
                        task_id=task.id,
                        recipients=recipients,
                        account_id=task.account_id,
                    )
                task.date_started = None
                task.date_completed = None
                task.status = TaskStatus.PENDING
                task.save(
                    update_fields=[
                        'date_started',
                        'date_completed',
                        'status',
                    ],
                )
                (
                    TaskPerformer.objects
                    .filter(task=task)
                    .exclude_directly_deleted()
                    .update(is_completed=False, date_completed=None)
                )
                deactivated_tasks.append(task)
            elif action_method.__name__ == ConditionAction.SKIP_TASK:
                # Child tasks can be active
                # because they are started after the parent task is skipped.
                deactivated_tasks.append(task)
        for task in deactivated_tasks:
            self._deactivate_task(parent_task=task)

    def _return_workflow_to_task(
        self,
        revert_from_tasks: Iterable[Task],
        revert_to_tasks: Iterable[Task],
    ):

        if not self.workflow.is_running:
            self.workflow.date_completed = None
            self.workflow.status = WorkflowStatus.RUNNING
            self.workflow.save(update_fields=['status', 'date_completed'])

        for revert_to_task in revert_to_tasks:
            action_method, by_condition = self.execute_conditions(
                revert_to_task,
            )
            if action_method:
                action_method(
                    task=revert_to_task,
                    is_returned=True,
                    by_condition=by_condition,
                )

        for revert_to_task in revert_to_tasks:
            self._deactivate_task(parent_task=revert_to_task)

        self.check_delay_workflow()

        if (
            WebHook.objects
            .on_account(self.account.id)
            .task_returned()
            .exists()
        ):
            for revert_from_task in revert_from_tasks:
                revert_from_task.refresh_from_db()
                send_task_returned_webhook.delay(
                    user_id=self.user.id,
                    account_id=self.account.id,
                    payload=revert_from_task.webhook_payload(),
                )

    def revert(
        self,
        comment: str,
        revert_from_task: Task,
    ) -> None:

        """ Can only be applied to a running workflow """

        if self.user.is_guest:
            raise exceptions.PermissionDenied
        if not revert_from_task.is_active:
            raise exceptions.RevertInactiveTask
        if self.workflow.is_running:
            if revert_from_task.sub_workflows.running().exists():
                raise exceptions.BlockedBySubWorkflows
        elif self.workflow.is_delayed:
            raise exceptions.DelayedWorkflowCannotBeChanged
        elif self.workflow.is_completed:
            raise exceptions.CompletedWorkflowCannotBeChanged

        task_performer = (
            TaskPerformer.objects
            .by_task(revert_from_task.id)
            .by_user_or_group(self.user.id)
            .exclude_directly_deleted()
            .first()
        )
        if task_performer:
            if task_performer.is_completed:
                raise exceptions.CompletedTaskCannotBeReturned
        elif not self.user.is_account_owner:
            raise exceptions.UserNotPerformer

        revert_to_tasks = revert_from_task.get_revert_tasks()
        self._validate_revert_is_possible(revert_to_tasks)

        with transaction.atomic():
            # Need run after update revert_to_task task (and performers)
            # and before start prev task
            clear_comment = MarkdownService.clear(comment)
            for revert_to_task in revert_to_tasks:
                WorkflowEventService.task_revert_event(
                    task=revert_to_task,
                    user=self.user,
                    text=comment,
                    clear_text=clear_comment,
                )
            AnalyticService.task_returned(
                user=self.user,
                task=revert_from_task,
                is_superuser=self.is_superuser,
                auth_type=self.auth_type,
            )
            self._return_workflow_to_task(
                revert_from_tasks=(revert_from_task,),
                revert_to_tasks=revert_to_tasks,
            )

    def return_to(self, revert_to_task: Optional[Task] = None):

        # validate revert to task
        if revert_to_task.is_pending:
            raise exceptions.ReturnToFutureTask
        action_method, _ = self.execute_conditions(revert_to_task)
        if (
            action_method is None  # Need different error text
            or action_method.__name__ == ConditionAction.SKIP_TASK
        ):
            raise exceptions.WorkflowActionServiceException(
                messages.MSG_PW_0079(revert_to_task.name),
            )

        # validate revert from tasks
        revert_from_tasks = self.workflow.tasks.active_or_delayed()
        if self.workflow.is_running:
            for revert_from_task in revert_from_tasks:
                if revert_from_task.sub_workflows.running().exists():
                    raise exceptions.BlockedBySubWorkflows

        with transaction.atomic():
            # Need run after update revert_to_task task (and performers)
            # and before start prev task
            WorkflowEventService.workflow_revert_event(
                task=revert_to_task,
                user=self.user,
            )
            AnalyticService.workflow_returned(
                user=self.user,
                task=revert_to_task,
                workflow=self.workflow,
                is_superuser=self.is_superuser,
                auth_type=self.auth_type,
            )
            self._return_workflow_to_task(
                revert_from_tasks=revert_from_tasks,
                revert_to_tasks=(revert_to_task,),
            )
