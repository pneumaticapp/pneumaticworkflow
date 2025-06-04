from typing import Optional, Callable, Tuple
from datetime import datetime
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from pneumatic_backend.processes.api_v2.services import (
    WorkflowEventService,
)
from django.db.models import Q
from pneumatic_backend.notifications.tasks import (
    send_new_task_notification,
    send_complete_task_notification,
)
from pneumatic_backend.processes.models import (
    Task,
    Workflow,
    TaskPerformer,
    Delay,
)
from pneumatic_backend.processes.tasks.webhooks import (
    send_task_completed_webhook,
    send_workflow_completed_webhook,
    send_task_returned_webhook,
    send_workflow_started_webhook,
)
from pneumatic_backend.webhooks.models import WebHook
from pneumatic_backend.processes.services.condition_check.service import (
    ConditionCheckService,
)
from pneumatic_backend.processes.services.websocket import WSSender
from pneumatic_backend.processes.enums import (
    WorkflowStatus,
    DirectlyStatus,
    TaskStatus,
)
from pneumatic_backend.authentication.services import GuestJWTAuthService
from pneumatic_backend.processes.api_v2.services.task.task import TaskService
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.services import exceptions
from pneumatic_backend.analytics.services import AnalyticService
from pneumatic_backend.notifications.tasks import (
    send_delayed_workflow_notification,
    send_resumed_workflow_notification,
)
from pneumatic_backend.processes.api_v2.services.task.field import (
    TaskFieldService
)
from pneumatic_backend.processes.messages import workflow as messages
from pneumatic_backend.services.markdown import MarkdownService

UserModel = get_user_model()


class WorkflowActionService:

    def __init__(
        self,
        user: UserModel,
        workflow: Workflow,
        is_superuser: bool = False,
        auth_type: AuthTokenType.LITERALS = AuthTokenType.USER,
        sync: bool = False
    ):
        self.workflow = workflow
        if user is None:
            raise Exception(
                'Specify user before initialization WorkflowActionService'
            )
        self.user = user
        self.is_superuser = is_superuser
        self.auth_type = auth_type
        self.sync = sync

    def _set_workflow_counts(
        self,
        force_save: bool = True,
        by_complete_task: bool = False,
        by_skip_task: bool = False,
    ):
        active_tasks_count = (
            self.workflow.tasks.exclude(status=TaskStatus.SKIPPED).count()
        )
        self.workflow.active_tasks_count = active_tasks_count
        count_skipped_tasks = self.workflow.tasks_count - active_tasks_count
        active_current_task = self.workflow.current_task - count_skipped_tasks

        if by_complete_task or by_skip_task:
            active_current_task = active_tasks_count
        elif active_current_task < 1:
            active_current_task = 1
        self.workflow.active_current_task = active_current_task
        if force_save:
            self.workflow.save(
                update_fields=('active_tasks_count', 'active_current_task')
            )

    def delay_workflow(self, delay: Delay, task: Task):

        """ Delay workflow from template delay """

        with transaction.atomic():
            # Snooze only task with template delay
            task.status = TaskStatus.DELAYED
            task.save(update_fields=['status'])
            delay.start_date = timezone.now()
            delay.save(update_fields=['start_date'])
            if not self.workflow.tasks.active().exists():
                self.workflow.status = WorkflowStatus.DELAYED
                self.workflow.save(update_fields=['status'])
            WorkflowEventService.workflow_delay_event(
                workflow=self.workflow,
                delay=delay
            )

    def force_delay_workflow(self, date: datetime):

        """ Create or update existent task delay with new duration """

        with transaction.atomic():
            self.workflow.status = WorkflowStatus.DELAYED
            self.workflow.save(update_fields=['status'])
            now = timezone.now()
            duration = date - now
            for task in self.workflow.tasks.active():
                task.status = TaskStatus.DELAYED
                task.save(update_fields=['status'])
                delay = Delay.objects.current_task_delay(task)
                if delay:
                    delay.directly_status = DirectlyStatus.CREATED
                    delay.duration = duration
                    delay.start_date = now
                    delay.save(
                        update_fields=[
                            'duration',
                            'start_date',
                            'directly_status'
                        ]
                    )
                else:
                    delay = Delay.objects.create(
                        task=task,
                        duration=duration,
                        start_date=now,
                        directly_status=DirectlyStatus.CREATED,
                    )
                users = (
                    TaskPerformer.objects
                    .filter(task_id=task.id)
                    .exclude_directly_deleted()
                    .not_completed()
                    .get_user_emails_and_ids_set()
                )
                # notifications about event
                for (user_id, user_email) in users:
                    send_delayed_workflow_notification.delay(
                        logging=self.user.account.log_api_requests,
                        logo_lg=self.user.account.logo_lg,
                        author_id=self.user.id,
                        user_id=user_id,
                        user_email=user_email,
                        account_id=self.user.account_id,
                        task_id=task.id,
                    )
                # decrease tasks count
                WSSender.send_removed_task_notification(
                    task=task,
                    user_ids=tuple(e[0] for e in users)
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
                duration=duration
            )

    def resume_workflow_with_new_current_task(self):

        """ Resume delayed workflow after
            remove task with delay in template """

        with transaction.atomic():
            self.workflow.status = WorkflowStatus.RUNNING
            self.workflow.save(update_fields=['status'])
            self.start_next_tasks(task=self.workflow.current_task_instance)

    def resume_workflow(self):

        """ Resume delayed workflow by timeout
            or after remove delay in template """

        if self.workflow.is_running:
            return
        elif self.workflow.is_completed:
            raise exceptions.ResumeNotDelayedWorkflow()

        with transaction.atomic():
            self.workflow.status = WorkflowStatus.RUNNING
            self.workflow.save(update_fields=['status'])
            task = self.workflow.current_task_instance
            delay = task.get_active_delay()
            if delay:
                delay.end_date = timezone.now()
                delay.save(update_fields=['end_date'])
            self.continue_task(task)

    def force_resume_workflow(self):

        """ Resume delayed workflow before the timeout """

        if self.workflow.is_running:
            return
        elif self.workflow.is_completed:
            raise exceptions.ResumeNotDelayedWorkflow()

        with transaction.atomic():
            self.workflow.status = WorkflowStatus.RUNNING
            self.workflow.save(update_fields=['status'])
            task = self.workflow.current_task_instance
            delay = task.get_active_delay()
            delay.end_date = timezone.now()
            delay.save(update_fields=['end_date'])
            WorkflowEventService.force_resume_workflow_event(
                workflow=self.workflow,
                user=self.user
            )
            send_resumed_workflow_notification.delay(
                logging=self.user.account.log_api_requests,
                logo_lg=self.user.account.logo_lg,
                author_id=self.user.id,
                account_id=self.user.account_id,
                task_id=task.id,
            )
            self.continue_task(task)

    def terminate_workflow(self):
        tasks_ids = list(self.workflow.tasks.only_ids())
        if self.workflow.is_delayed:
            Delay.objects.current_task_delay_qst(
                self.workflow.current_task_instance
            ).update(end_date=timezone.now())

        task = self.workflow.current_task_instance
        user_ids = tuple(
            TaskPerformer.objects.filter(task_id=task.id,)
            .exclude_directly_deleted()
            .not_completed()
            .get_user_ids_set()
        )
        WSSender.send_removed_task_notification(
            task=task,
            user_ids=user_ids
        )
        for task_id in tasks_ids:
            GuestJWTAuthService.deactivate_task_guest_cache(
                task_id=task_id
            )
        AnalyticService.workflows_terminated(
            user=self.user,
            workflow=self.workflow,
            is_superuser=self.is_superuser,
            auth_type=self.auth_type
        )
        self.workflow.delete()

    def end_process(
        self,
        task: Task = None,
        is_returned: bool = False,
        by_condition: bool = True,
        by_complete_task: bool = False,
        by_skip_task: bool = False,
    ):

        task = self.workflow.current_task_instance
        if self.workflow.is_delayed:
            Delay.objects.current_task_delay_qst(
                task
            ).update(end_date=timezone.now())
        tasks_ids = self.workflow.tasks.only_ids()
        for task_id in tasks_ids:
            GuestJWTAuthService.deactivate_task_guest_cache(
                task_id=task_id
            )

        update_fields = ['status', 'date_completed', 'current_task']
        if self.workflow.is_urgent:
            self.workflow.is_urgent = False
            update_fields.append('is_urgent')
            Task.objects.filter(id__in=tasks_ids).update(is_urgent=False)
        self.workflow.status = WorkflowStatus.DONE
        self.workflow.date_completed = timezone.now()
        self.workflow.save(update_fields=update_fields)
        if by_condition:
            WorkflowEventService.workflow_ended_by_condition_event(
                workflow=self.workflow,
                user=self.user,
            )
        elif by_complete_task:
            WorkflowEventService.workflow_complete_event(
                workflow=self.workflow,
                user=self.user
            )
            AnalyticService.workflow_completed(
                user=self.user,
                is_superuser=self.is_superuser,
                auth_type=self.auth_type,
                workflow=self.workflow
            )
            # WSSender.send_removed_task_notification
            # sent in complete_task action
        else:
            # if workflow force ended
            WorkflowEventService.workflow_ended_event(
                workflow=self.workflow,
                user=self.user,
            )
            user_ids = tuple(
                TaskPerformer.objects.filter(task_id=task.id,)
                .exclude_directly_deleted()
                .not_completed()
                .get_user_ids_set()
            )
            WSSender.send_removed_task_notification(
                task=task,
                user_ids=user_ids
            )
        acc_id = self.user.account_id
        self._set_workflow_counts(
            by_complete_task=by_complete_task,
            by_skip_task=by_skip_task,
        )
        if WebHook.objects.on_account(acc_id).wf_completed().exists():
            send_workflow_completed_webhook.delay(
                user_id=self.user.id,
                account_id=self.user.account_id,
                payload=self.workflow.webhook_payload()
            )

    def skip_task(
        self,
        task: Task,
        is_returned: bool = False,
        by_condition: bool = True,
        by_complete_task: bool = False,
        need_insert_fields_values: bool = True,
    ):
        if need_insert_fields_values:
            task_service = TaskService(
                instance=task,
                user=self.user or self.workflow.account.get_owner()
            )
            fields_values = self.workflow.get_fields_markdown_values(
                tasks_filter_kwargs={'number__lt': task.number},
            )
            task_service.insert_fields_values(fields_values=fields_values)

        WorkflowEventService.task_skip_event(task)
        if is_returned and task.number != 1:
            task.status = TaskStatus.PENDING
            next_task = task.prev
        else:
            task.status = TaskStatus.SKIPPED
            next_task = task.next
        task.save(update_fields=['status'])
        self._set_workflow_counts(by_skip_task=True)
        self.start_next_tasks(
            task=next_task,
            is_returned=is_returned,
            by_complete_task=by_complete_task,
        )

    def execute_condition(self, task: Task) -> Tuple[Callable, bool]:

        """ Return pair:
            - method : condition_result or default start_task
            - marker, that indicates if method selected by condition """

        for condition in task.conditions.all():
            condition_result = ConditionCheckService.check(
                condition=condition,
                workflow_id=task.workflow_id,
            )
            if condition_result:
                return getattr(self, f'{condition.action}'), True
            elif condition.action == 'start_task':
                return self.skip_task, True
        return self.start_task, False

    def start_workflow(self):

        # Duplicate start task code, need for workflow_run_event
        task = self.workflow.current_task_instance
        task_service = TaskService(instance=task,  user=self.user)
        fields_values = self.workflow.get_fields_markdown_values(
            tasks_filter_kwargs={'number__lt': task.number},
        )
        task_service.insert_fields_values(fields_values=fields_values)

        WorkflowEventService.workflow_run_event(
            workflow=self.workflow,
            user=self.user
        )
        if self.workflow.ancestor_task:
            WorkflowEventService.sub_workflow_run_event(
                workflow=self.workflow.ancestor_task.workflow,
                sub_workflow=self.workflow,
                user=self.user
            )
        self.start_next_tasks(task=self.workflow.current_task_instance)
        if WebHook.objects.on_account(
            self.user.account.id
        ).wf_started().exists():
            send_workflow_started_webhook.delay(
                user_id=self.user.id,
                account_id=self.user.account.id,
                payload=self.workflow.webhook_payload()
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
        task_service = TaskService(
            instance=task,
            user=self.user
        )
        task_service.partial_update(
            is_urgent=self.workflow.is_urgent,
            date_completed=None,
            status=TaskStatus.ACTIVE,
            date_started=timezone.now(),
            force_save=True
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

        if (
            self.workflow.is_legacy_template
            or not self.workflow.template.is_onboarding
        ):
            recipients_qst = TaskPerformer.objects.filter(
                user__is_new_tasks_subscriber=True,
                task_id=task.id,
            ).exclude_directly_deleted().only(
                'user_id',
                'user__email'
            ).order_by('id')
            if self.workflow.current_task == 1 and not is_returned:
                recipients_qst = recipients_qst.exclude(
                    user_id=self.workflow.workflow_starter_id
                )
            recipients = [(el.user_id, el.user.email) for el in recipients_qst]
            wf_starter = self.workflow.workflow_starter
            wf_starter_name = wf_starter.name if wf_starter else None
            wf_starter_photo = wf_starter.photo if wf_starter else None

            # Email and Push notification
            send_new_task_notification.delay(
                logging=self.user.account.log_api_requests,
                account_id=self.user.account_id,
                recipients=recipients,
                task_id=task.id,
                task_name=task.name,
                task_description=task.description,
                workflow_name=self.workflow.name,
                template_name=self.workflow.get_template_name(),
                workflow_starter_name=wf_starter_name,
                workflow_starter_photo=wf_starter_photo,
                due_date_timestamp=(
                    task.due_date.timestamp() if task.due_date else None
                ),
                logo_lg=task.account.logo_lg,
                is_returned=is_returned,
            )
        # Websocket notification
        WSSender.send_new_task_notification(task=task, sync=self.sync)
        for task_id in self.workflow.tasks.filter(
            number__lte=task.number
        ).only_ids():
            GuestJWTAuthService.delete_task_guest_cache(
                task_id=task_id
            )

    def start_next_tasks(
        self,
        task: Task = None,
        is_returned: bool = False,
        by_complete_task: bool = False,
    ):

        # TODO Method will run all available parallel tasks

        if is_returned:
            if task:
                action_method, _ = self.execute_condition(task)
                if action_method:
                    action_method(
                        task=task,
                        is_returned=True,
                    )
        else:
            if task:
                action_method, by_condition = self.execute_condition(task)
                if action_method:
                    action_method(
                        task=task,
                        is_returned=is_returned,
                        by_condition=by_condition,
                        by_complete_task=by_complete_task,
                    )
            else:
                self.end_process(
                    by_condition=False,
                    by_complete_task=by_complete_task,
                )

    def start_task(
        self,
        task: Task,
        is_returned: bool = False,
        by_condition: bool = True,
        by_complete_task: bool = False,
        need_insert_fields_values: bool = True,
    ):

        self.workflow.current_task = task.number
        self._set_workflow_counts(force_save=False)
        self.workflow.save(
            update_fields=(
                'current_task',
                'active_current_task',
                'active_tasks_count',
            )
        )
        task_service = TaskService(
            instance=task,
            user=self.user or self.workflow.account.get_owner()
        )
        fields_values = self.workflow.get_fields_markdown_values(
            tasks_filter_kwargs={'number__lt': task.number},
        )
        task_service.insert_fields_values(fields_values=fields_values)
        task.update_performers(restore_performers=True)
        task_performers_exists = (
            TaskPerformer.objects.exclude_directly_deleted().by_task(
                task.id
            ).exists()
        )
        if not task_performers_exists:
            WorkflowEventService.task_skip_no_performers_event(task)
            task.status = TaskStatus.SKIPPED
            task.save(update_fields=('status',))
            next_task = task.prev if is_returned else task.next
            self.start_next_tasks(
                task=next_task,
                is_returned=is_returned,
                by_complete_task=by_complete_task,
            )
        else:
            delay = Delay.objects.current_task_delay(task)
            if delay:
                self.delay_workflow(delay=delay, task=task)
            else:
                self.continue_workflow(task=task, is_returned=is_returned)

    def complete_task(self, task: Task, by_user: bool = False):

        """ Complete workflow task if it <= current task
            Only for current task run complete actions """

        if task.number > self.workflow.current_task:
            return
        current_date = timezone.now()
        update_fields = {
            'status': TaskStatus.COMPLETED,
            'date_completed': current_date,
            'date_started': task.date_started or current_date
        }
        task_service = TaskService(
            instance=task,
            is_superuser=self.is_superuser,
            auth_type=self.auth_type,
            user=self.user
        )
        task_service.partial_update(**update_fields, force_save=True)
        if task.number != self.workflow.current_task:
            return
        # Not include guests
        performers_ids = (
            TaskPerformer.objects.by_task(task.id)
            .exclude_directly_deleted()
            .not_completed()
            .users()
            .values_list('id', flat=True)
        )
        task_performer_ids = (
            UserModel.objects
            .get_users_in_performer(performers_ids=performers_ids)
            .exclude_directly_deleted()
            .order_by('id')
            .user_ids_set()
        )
        WSSender.send_removed_task_notification(
            task=task,
            user_ids=task_performer_ids,
            sync=self.sync
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
                logging=self.user.account.log_api_requests,
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
                is_completed=True
            )
        )
        if by_user:
            AnalyticService.task_completed(
                user=self.user,
                is_superuser=self.is_superuser,
                auth_type=self.auth_type,
                workflow=self.workflow,
                task=task
            )
            # Need run after save completed task (and performers)
            # and before start next tasks
            WorkflowEventService.task_complete_event(
                task=task,
                user=self.user
            )
        self.start_next_tasks(
            task=task.next,
            by_complete_task=True
        )
        acc_id = self.user.account.id
        if WebHook.objects.on_account(acc_id).task_completed().exists():
            send_task_completed_webhook.delay(
                user_id=self.user.id,
                account_id=self.user.account_id,
                payload=task.webhook_payload()
            )

    def _task_can_be_completed(self, task: Task) -> bool:

        """ Implies that the specified user has completed the task """

        if task.is_completed is True:
            return False
        else:
            task_performers = (
                task.taskperformer_set.exclude_directly_deleted()
            )
            completed_performers = task_performers.filter(
                Q(is_completed=True)
                | Q(is_completed=False, user_id=self.user.id)
                | Q(is_completed=False, group__users=self.user.id)
            ).exists()
            incompleted_performers = task_performers.not_completed().exclude(
                Q(user_id=self.user.id)
                | Q(is_completed=False, group__users=self.user.id)
            ).exists()
            by_all = task.require_completion_by_all
            return (
                not by_all and completed_performers or
                by_all and not incompleted_performers
            )

    def complete_task_for_user(
        self,
        task: Task,
        fields_values: Optional[dict] = None,
    ):
        if self.workflow.is_delayed:
            raise exceptions.CompleteDelayedWorkflow()
        elif self.workflow.is_completed:
            raise exceptions.CompleteCompletedWorkflow()
        if not task.is_active:
            raise exceptions.CompleteInactiveTask()

        task_performer = (
            TaskPerformer.objects
            .by_task(task.id)
            .by_user_or_group(self.user.id)
            .exclude_directly_deleted()
            .first()
        )
        if task_performer:
            if task_performer.is_completed:
                raise exceptions.UserAlreadyCompleteTask()
        elif not self.user.is_account_owner:
            raise exceptions.UserNotPerformer()

        if not task.checklists_completed:
            raise exceptions.ChecklistIncompleted()
        elif task.sub_workflows.running().exists():
            raise exceptions.SubWorkflowsIncompleted()

        fields_values = fields_values or dict()
        with transaction.atomic():
            for task_field in task.output.all():
                service = TaskFieldService(
                    user=self.user,
                    instance=task_field
                )
                service.partial_update(
                    value=fields_values.get(task_field.api_name),
                    force_save=True
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
                        update_fields=('date_completed', 'is_completed')
                    )
                    if not self.user.is_guest:
                        # Websocket notification
                        WSSender.send_removed_task_notification(
                            task=task,
                            user_ids=(self.user.id,),
                            sync=self.sync
                        )
            elif self.user.is_account_owner:
                # account owner force completion
                # not complete performers, but send ws remove task
                self.complete_task(task=task, by_user=True)
        return task

    def _task_is_returnable(self, task: Task):
        service = WorkflowActionService(
            user=self.user,
            workflow=self.workflow
        )
        action_method, _ = service.execute_condition(task)
        if action_method.__name__ == 'skip_task':
            if task.number == 1:
                return False
            return self._task_is_returnable(task=task.prev)
        return True

    def _return_workflow_to_task(
        self,
        revert_from_task: Task,
        revert_to_task: Task,
    ):

        """ Return workflow to specific task """

        next_tasks = self.workflow.tasks.filter(
            number__gt=revert_to_task.number
        )
        next_tasks.update(
            date_started=None,
            date_completed=None,
            status=TaskStatus.PENDING,
        )
        (
            TaskPerformer.objects
            .with_tasks_after(revert_to_task)
            .by_workflow(self.workflow.id)
            .exclude_directly_deleted()
            .update(is_completed=False, date_completed=None)
        )
        Delay.objects.filter(
            task__in=next_tasks,
            directly_status=DirectlyStatus.NO_STATUS
        ).update(
            start_date=None,
            end_date=None,
            estimated_end_date=None,
        )
        workflow_is_running = self.workflow.is_running

        # update workflow logic
        update_fields = ['current_task']
        if self.workflow.is_delayed:
            delay = revert_from_task.get_active_delay()
            if delay:
                delay.end_date = timezone.now()
                if delay.directly_status:
                    delay.save(update_fields=['end_date'])
                else:
                    revert_from_task.reset_delay(delay)
        if not self.workflow.is_running:
            self.workflow.date_completed = None
            self.workflow.status = WorkflowStatus.RUNNING
            update_fields.append('status')
            update_fields.append('date_completed')

        self.workflow.current_task -= 1

        if revert_to_task is not None:
            self.workflow.current_task = revert_to_task.number

        self.workflow.save(update_fields=update_fields)
        if workflow_is_running:
            WSSender.send_removed_task_notification(revert_from_task)

        # end update workflow logic
        action_method, by_cond = self.execute_condition(revert_to_task)
        action_method(
            task=revert_to_task,
            is_returned=True,
            by_condition=by_cond,
        )

        acc_id = self.user.account_id
        self._set_workflow_counts()
        if WebHook.objects.on_account(acc_id).task_returned().exists():
            revert_from_task.refresh_from_db()
            send_task_returned_webhook.delay(
                user_id=self.user.id,
                account_id=acc_id,
                payload=revert_from_task.webhook_payload()
            )

    def revert(
        self,
        comment: str,
        revert_from_task: Task
    ) -> None:

        """ Can only be applied to a running workflow """

        if self.user.is_guest:
            raise exceptions.PermissionDenied()
        if revert_from_task.number == 1:
            raise exceptions.FirstTaskCannotBeReverted()
        if not revert_from_task.is_active:
            raise exceptions.RevertInactiveTask()
        revert_to_task = revert_from_task.prev
        if self.workflow.is_running:
            if revert_from_task.sub_workflows.running().exists():
                raise exceptions.BlockedBySubWorkflows()
        elif self.workflow.is_delayed:
            raise exceptions.DelayedWorkflowCannotBeChanged()
        elif self.workflow.is_completed:
            raise exceptions.CompletedWorkflowCannotBeChanged()

        task_performer = (
            TaskPerformer.objects
            .by_task(revert_from_task.id)
            .by_user_or_group(self.user.id)
            .exclude_directly_deleted()
            .first()
        )
        if task_performer:
            if task_performer.is_completed:
                raise exceptions.CompletedTaskCannotBeReturned()
        elif not self.user.is_account_owner:
            raise exceptions.UserNotPerformer()

        action_method, _ = self.execute_condition(revert_to_task)
        if action_method.__name__ == 'skip_task':
            if revert_to_task.number == 1:
                raise exceptions.WorkflowActionServiceException(
                    messages.MSG_PW_0079(revert_to_task.name)
                )
            if not self._task_is_returnable(revert_to_task.prev):
                raise exceptions.WorkflowActionServiceException(
                    messages.MSG_PW_0080(revert_to_task.name)
                )
        clear_comment = MarkdownService.clear(comment)
        with transaction.atomic():
            # Need run after update revert_to_task task (and performers)
            # and before start prev task
            WorkflowEventService.task_revert_event(
                task=revert_to_task,
                user=self.user,
                text=comment,
                clear_text=clear_comment
            )
            AnalyticService.task_returned(
                user=self.user,
                task=revert_from_task,
                is_superuser=self.is_superuser,
                auth_type=self.auth_type
            )
            self._return_workflow_to_task(
                revert_from_task=revert_from_task,
                revert_to_task=revert_to_task,
            )

    def return_to(self, revert_to_task: Optional[Task] = None):

        revert_from_task = self.workflow.current_task_instance
        if self.workflow.is_running:
            if revert_from_task.sub_workflows.running().exists():
                raise exceptions.BlockedBySubWorkflows()
            if revert_to_task.number >= revert_from_task.number:
                raise exceptions.ReturnToFutureTask()
        else:
            if revert_to_task.number > revert_from_task.number:
                raise exceptions.ReturnToFutureTask()

        action_method, _ = self.execute_condition(revert_to_task)
        if action_method.__name__ == 'skip_task':
            raise exceptions.WorkflowActionServiceException(
                messages.MSG_PW_0079(revert_to_task.name)
            )

        with transaction.atomic():
            # Need run after update revert_to_task task (and performers)
            # and before start prev task
            WorkflowEventService.workflow_revert_event(
                task=revert_from_task,
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
                revert_from_task=revert_from_task,
                revert_to_task=revert_to_task,
            )
