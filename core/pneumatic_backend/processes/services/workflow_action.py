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
    Condition,
    TaskPerformer,
    Delay,
)
from pneumatic_backend.processes.tasks.webhooks import (
    send_task_completed_webhook,
    send_workflow_completed_webhook,
    send_task_returned_webhook,
)
from pneumatic_backend.webhooks.models import WebHook
from pneumatic_backend.processes.services.condition_check.service import (
    ConditionCheckService,
)
from pneumatic_backend.processes.services.websocket import WSSender
from pneumatic_backend.processes.enums import (
    WorkflowStatus,
    DirectlyStatus,
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


UserModel = get_user_model()


class WorkflowActionService:

    def __init__(
        self,
        user: UserModel,
        is_superuser: bool = False,
        auth_type: AuthTokenType = AuthTokenType.USER,
        sync: bool = False
    ):
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
        workflow: Workflow,
        force_save: bool = True,
        by_complete_task: bool = False,
        by_skip_task: bool = False,
    ):
        active_tasks_count = (
            workflow.tasks.filter(is_skipped=False).count()
        )
        workflow.active_tasks_count = active_tasks_count
        count_skipped_tasks = workflow.tasks_count - active_tasks_count
        active_current_task = workflow.current_task - count_skipped_tasks

        if by_complete_task or by_skip_task:
            active_current_task = active_tasks_count
        elif active_current_task < 1:
            active_current_task = 1
        workflow.active_current_task = active_current_task
        if force_save:
            workflow.save(
                update_fields=('active_tasks_count', 'active_current_task')
            )

    def delay_workflow(
        self,
        workflow: Workflow,
        delay: Delay
    ):
        """ Delay workflow from template delay """

        with transaction.atomic():

            workflow.status = WorkflowStatus.DELAYED
            workflow.save(update_fields=['status'])
            delay.start_date = timezone.now()
            delay.save(update_fields=['start_date'])
            WorkflowEventService.workflow_delay_event(
                workflow=workflow,
                delay=delay
            )

    def force_delay_workflow(
        self,
        date: datetime,
        workflow: Workflow
    ):

        """ Create or update existent task delay with new duration """

        with transaction.atomic():
            workflow.status = WorkflowStatus.DELAYED
            workflow.save(update_fields=['status'])
            now = timezone.now()
            duration = date - now
            task = workflow.current_task_instance
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

            WorkflowEventService.force_delay_workflow_event(
                workflow=workflow,
                user=self.user,
                delay=delay,
            )
            users = (
                TaskPerformer.objects
                .filter(task_id=task.id)
                .exclude_directly_deleted()
                .not_completed()
                .users()
                .values_list('user_id', 'user__email')
            )
            # notifications about event
            for (user_id, user_email) in users:
                send_delayed_workflow_notification.delay(
                    logging=self.user.account.log_api_requests,
                    logo_lg=self.user.account.logo_lg,
                    task_id=task.id,
                    author_id=self.user.id,
                    user_id=user_id,
                    user_email=user_email,
                    account_id=self.user.account_id,
                    workflow_name=workflow.name,
                )
            # decrease tasks count
            WSSender.send_removed_task_notification(
                task=task,
                user_ids=tuple(e[0] for e in users)
            )

            AnalyticService.workflow_delayed(
                user=self.user,
                workflow=workflow,
                task=task,
                is_superuser=self.is_superuser,
                auth_type=self.auth_type,
                duration=duration
            )

    def resume_workflow_with_new_current_task(
        self,
        workflow: Workflow
    ):

        """ Resume delayed workflow after
            remove task with delay in template """

        with transaction.atomic():
            workflow.status = WorkflowStatus.RUNNING
            workflow.save(update_fields=['status'])
            task = workflow.current_task_instance
            action_method, by_cond = self.execute_condition(task)
            action_method(
                workflow=workflow,
                task=task,
                user=self.user,
                by_condition=by_cond,
            )

    def resume_workflow(
        self,
        workflow: Workflow
    ):

        """ Resume delayed workflow by timeout
            or after remove delay in template """

        if workflow.is_running:
            return
        elif workflow.is_completed:
            raise exceptions.ResumeNotDelayedWorkflow()

        with transaction.atomic():
            workflow.status = WorkflowStatus.RUNNING
            workflow.save(update_fields=['status'])
            task = workflow.current_task_instance
            delay = task.get_active_delay()
            if delay:
                delay.end_date = timezone.now()
                delay.save(update_fields=['end_date'])
            self.continue_task(
                workflow=workflow,
                task=task,
            )

    def force_resume_workflow(
        self,
        workflow: Workflow
    ):

        """ Resume delayed workflow before the timeout """

        if workflow.is_running:
            return
        elif workflow.is_completed:
            raise exceptions.ResumeNotDelayedWorkflow()

        with transaction.atomic():
            workflow.status = WorkflowStatus.RUNNING
            workflow.save(update_fields=['status'])
            task = workflow.current_task_instance
            delay = task.get_active_delay()
            delay.end_date = timezone.now()
            delay.save(update_fields=['end_date'])
            WorkflowEventService.force_resume_workflow_event(
                workflow=workflow,
                user=self.user
            )
            send_resumed_workflow_notification.delay(
                logging=self.user.account.log_api_requests,
                logo_lg=self.user.account.logo_lg,
                task_id=task.id,
                author_id=self.user.id,
                account_id=self.user.account_id,
                workflow_name=workflow.name,
            )
            self.continue_task(
                workflow=workflow,
                task=task,
            )

    def terminate_workflow(
        self,
        workflow: Workflow,
        **kwargs
    ):
        tasks_ids = list(workflow.tasks.only_ids())
        if workflow.status == WorkflowStatus.DELAYED:
            Delay.objects.current_task_delay_qst(
                workflow.current_task_instance
            ).update(end_date=timezone.now())

        task = workflow.current_task_instance
        user_ids = TaskPerformer.objects.filter(
            task_id=task.id,
        ).exclude_directly_deleted().not_completed().users().user_ids()
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
            workflow=workflow,
            is_superuser=self.is_superuser,
            auth_type=self.auth_type
        )
        workflow.delete()

    def end_process(
        self,
        workflow: Workflow,
        by_condition: bool = True,
        by_complete_task: bool = False,
        by_skip_task: bool = False,
        **kwargs
    ):

        task = workflow.current_task_instance
        if workflow.status == WorkflowStatus.DELAYED:
            Delay.objects.current_task_delay_qst(
                task
            ).update(end_date=timezone.now())
        tasks_ids = workflow.tasks.only_ids()
        for task_id in tasks_ids:
            GuestJWTAuthService.deactivate_task_guest_cache(
                task_id=task_id
            )

        update_fields = ['status', 'date_completed', 'current_task']
        if workflow.is_urgent:
            workflow.is_urgent = False
            update_fields.append('is_urgent')
            Task.objects.filter(id__in=tasks_ids).update(is_urgent=False)
        workflow.status = WorkflowStatus.DONE
        workflow.date_completed = timezone.now()
        workflow.save(update_fields=update_fields)
        if by_condition:
            WorkflowEventService.workflow_ended_by_condition_event(
                workflow=workflow,
                user=self.user,
            )
        elif by_complete_task:
            WorkflowEventService.workflow_complete_event(
                workflow=workflow,
                user=self.user,
            )
            AnalyticService.workflow_completed(
                user=self.user,
                is_superuser=self.is_superuser,
                auth_type=self.auth_type,
                workflow=workflow
            )
            # WSSender.send_removed_task_notification
            # sent in complete_task action
        else:
            # if workflow force ended
            WorkflowEventService.workflow_ended_event(
                workflow=workflow,
                user=self.user,
            )
            user_ids = TaskPerformer.objects.filter(
                task_id=task.id,
            ).exclude_directly_deleted().not_completed().users().user_ids()
            WSSender.send_removed_task_notification(
                task=task,
                user_ids=user_ids
            )
        acc_id = self.user.account_id
        self._set_workflow_counts(
            workflow=workflow,
            by_complete_task=by_complete_task,
            by_skip_task=by_skip_task,
        )
        if WebHook.objects.on_account(acc_id).wf_completed().exists():
            send_workflow_completed_webhook.delay(
                user_id=self.user.id,
                account_id=self.user.account_id,
                payload=workflow.webhook_payload()
            )

    def skip_task(
        self,
        workflow: Workflow,
        task: Task,
        is_reverted: Optional[bool] = None,
        need_insert_fields_values: bool = True,
        **kwargs,
    ):
        if need_insert_fields_values:
            task_service = TaskService(
                instance=task,
                user=self.user or workflow.account.get_owner()
            )
            fields_values = workflow.get_fields_markdown_values(
                tasks_filter_kwargs={'number__lt': task.number},
            )
            task_service.insert_fields_values(fields_values=fields_values)

        WorkflowEventService.task_skip_event(task)
        if is_reverted and task.number != 1:
            next_task = task.prev
            task.is_skipped = False
        else:
            next_task = task.next
            task.is_skipped = True
            is_reverted = False
        task.save(update_fields=['is_skipped'])
        self._set_workflow_counts(workflow, by_skip_task=True)
        if next_task:
            action_method, _ = self.execute_condition(next_task)
            if action_method:
                action_method(
                    workflow=workflow,
                    task=next_task,
                    is_reverted=is_reverted,
                )
            else:
                self.start_task(workflow=workflow, task=next_task)
        else:
            self.end_process(
                workflow=workflow,
                by_condition=False,
                by_skip_task=True,
            )

    def skip_task_no_performers(
        self,
        task: Task,
        **kwargs
    ):
        WorkflowEventService.task_skip_no_performers_event(task)
        next_task = task.next
        task.is_skipped = True
        task.save(update_fields=('is_skipped',))
        workflow = task.workflow
        self._set_workflow_counts(workflow, by_skip_task=True)
        user = workflow.workflow_starter
        if next_task:
            action_method, by_cond = self.execute_condition(next_task)
            if action_method:
                action_method(
                    workflow=workflow,
                    task=next_task,
                    user=user,
                    by_condition=by_cond,
                )
            else:
                self.start_task(workflow=workflow, task=next_task)
        else:
            self.end_process(
                workflow=workflow,
                by_condition=False
            )

    def execute_condition(self, task: Task) -> Tuple[Callable, bool]:

        """ Return pair:
            - method : condition_result or default start_task
            - marker, that indicates if method selected by condition """

        method = self.start_task
        for condition in task.conditions.all():
            condition_result = ConditionCheckService.check(
                condition=condition,
                workflow_id=task.workflow_id,
            )
            if condition_result:
                return getattr(self, f'{condition.action}'), True
            elif condition.action == Condition.START_TASK:
                return self.skip_task, True
        return method, False

    def start_workflow(
        self,
        workflow: Workflow
    ):
        task = workflow.current_task_instance
        task_service = TaskService(instance=task, user=self.user)
        fields_values = workflow.get_fields_markdown_values(
            tasks_filter_kwargs={'number__lt': task.number},
        )
        # Workflow run event need task with inserted vars
        task_service.insert_fields_values(fields_values=fields_values)

        WorkflowEventService.workflow_run_event(
            workflow=workflow,
            user=self.user
        )
        if workflow.ancestor_task:
            WorkflowEventService.sub_workflow_run_event(
                workflow=workflow.ancestor_task.workflow,
                sub_workflow=workflow,
                user=self.user
            )
        action_method, by_cond = self.execute_condition(task)
        action_method(
            workflow=workflow,
            task=task,
            user=self.user,
            by_condition=by_cond,
            need_insert_fields_values=False,
            send_new_task_notification=False
        )

    def continue_workflow(
        self,
        workflow: Workflow,
        task: Task,
        is_returned: bool = False,
    ):
        if not workflow.is_running:
            workflow.status = WorkflowStatus.RUNNING
            workflow.save(update_fields=['status'])
        workflow.members.add(*task.performers.all())
        self.continue_task(
            workflow=workflow,
            task=task,
            is_returned=is_returned,
        )

    def continue_task(
        self,
        workflow: Workflow,
        task: Task,
        is_returned: bool = False,
    ):

        """ Continue start task after run or workflow delay """
        user = self.user or workflow.account.get_owner()
        task_start_event_already_exist = (
            not is_returned and bool(task.date_started)
        )
        task_service = TaskService(
            instance=task,
            user=user
        )
        task_service.partial_update(
            is_urgent=workflow.is_urgent,
            is_completed=False,
            date_completed=None,
            is_skipped=False,
            date_started=timezone.now(),
            force_save=True
        )
        task_service.set_due_date_from_template()
        TaskPerformer.objects.by_workflow(
            workflow.id
        ).with_tasks_after(
            task
        ).update(
            is_completed=False,
            date_completed=None
        )
        # if task force snoozed then start task event already exists
        # but if task returned then
        if not task_start_event_already_exist:
            WorkflowEventService.task_started_event(task)

        if workflow.is_legacy_template or not workflow.template.is_onboarding:
            recipients_qst = TaskPerformer.objects.filter(
                user__is_new_tasks_subscriber=True,
                task_id=task.id,
            ).exclude_directly_deleted().only(
                'user_id',
                'user__email'
            ).order_by('id')
            if workflow.current_task == 1 and not is_returned:
                recipients_qst = recipients_qst.exclude(
                    user_id=workflow.workflow_starter_id
                )
            recipients = [(el.user_id, el.user.email) for el in recipients_qst]
            wf_starter = workflow.workflow_starter
            wf_starter_name = wf_starter.name if wf_starter else None
            wf_starter_photo = wf_starter.photo if wf_starter else None

            # Email and Push notification
            send_new_task_notification.delay(
                logging=user.account.log_api_requests,
                account_id=user.account_id,
                recipients=recipients,
                task_id=task.id,
                task_name=task.name,
                task_description=task.description,
                workflow_name=workflow.name,
                template_name=workflow.get_template_name(),
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
        for task_id in workflow.tasks.filter(
            number__lte=task.number
        ).only_ids():
            GuestJWTAuthService.delete_task_guest_cache(
                task_id=task_id
            )

    def start_task(
        self,
        workflow: Workflow,
        task: Task,
        need_insert_fields_values: bool = True,
        **kwargs,
    ):

        workflow.current_task = task.number
        self._set_workflow_counts(workflow, force_save=False)
        workflow.save(
            update_fields=(
                'current_task',
                'active_current_task',
                'active_tasks_count',
            )
        )
        if need_insert_fields_values:
            task_service = TaskService(
                instance=task,
                user=self.user or workflow.account.get_owner()
            )
            fields_values = workflow.get_fields_markdown_values(
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
            self.skip_task_no_performers(task)
        else:
            delay = Delay.objects.current_task_delay(task)
            if delay:
                self.delay_workflow(
                    workflow=workflow,
                    delay=delay,
                )
            else:
                self.continue_workflow(
                    workflow=workflow,
                    task=task,
                    is_returned=kwargs.get('is_reverted', False)
                )

    def complete_task(
        self,
        task: Task,
    ):

        """ Complete workflow task if it <= current task
            Only for current task run complete actions """

        workflow = task.workflow
        if task.number > workflow.current_task:
            return
        current_date = timezone.now()
        update_fields = {
            'is_completed': True,
            'date_completed': current_date,
        }
        if not task.date_started:
            update_fields['date_started'] = current_date
        task_service = TaskService(
            instance=task,
            is_superuser=self.is_superuser,
            auth_type=self.auth_type,
            user=self.user
        )
        task_service.partial_update(**update_fields, force_save=True)
        if task.number == workflow.current_task:
            # Not include guests
            removed_task_users_qst = (
                TaskPerformer.objects.by_task(task.id)
                .exclude_directly_deleted()
                .not_completed()
                .users()
                .order_by('user_id')
            )
            removed_task_users_user_ids = removed_task_users_qst.user_ids()
            WSSender.send_removed_task_notification(
                task=task,
                user_ids=removed_task_users_user_ids,
                sync=self.sync
            )
            notification_recipients = [
                (el.user_id, el.user.email) for el in (
                    removed_task_users_qst
                    .filter(user__is_complete_tasks_subscriber=True)
                    .exclude(user_id=self.user.id)
                )
            ]
            if notification_recipients:
                send_complete_task_notification.delay(
                    logging=self.user.account.log_api_requests,
                    author_id=self.user.id,
                    account_id=task.account_id,
                    recipients=notification_recipients,
                    task_id=task.id,
                    task_name=task.name,
                    workflow_name=workflow.name,
                    logo_lg=task.account.logo_lg,
                )
            acc_id = self.user.account.id
            if WebHook.objects.on_account(acc_id).task_completed().exists():
                send_task_completed_webhook.delay(
                    user_id=self.user.id,
                    account_id=self.user.account_id,
                    payload=task.webhook_payload()
                )
            if task.number == workflow.tasks_count:
                self.end_process(
                    workflow=workflow,
                    by_condition=False,
                    by_complete_task=True
                )
            else:
                next_task = task.next
                action_method, by_cond = self.execute_condition(next_task)
                action_method(
                    workflow=workflow,
                    task=next_task,
                    user=self.user,
                    by_condition=by_cond,
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
            ).exists()
            incompleted_performers = task_performers.not_completed().exclude(
                user_id=self.user.id
            ).exists()
            by_all = task.require_completion_by_all
            return (
                not by_all and completed_performers or
                by_all and not incompleted_performers
            )

    def complete_current_task_for_user(
        self,
        workflow: Workflow,
        fields_values: Optional[dict] = None,
    ):

        """ Complete current task for a specific user.
            Validate completion and run all completion actions """

        task = workflow.current_task_instance
        task_fields = list(task.output.all())
        for task_field in task_fields:
            service = TaskFieldService(
                user=self.user,
                instance=task_field
            )
            service.partial_update(
                value=fields_values.get(task_field.api_name),
                force_save=True
            )

        task_performers_qst = (
            TaskPerformer.objects
            .by_task(task.id)
            .exclude_directly_deleted()
            .order_by('user_id')
        )
        task_performer = task_performers_qst.by_user(self.user.id).first()
        if not task_performer and not self.user.is_account_owner:
            raise exceptions.UserNotPerformer()

        AnalyticService.task_completed(
            user=self.user,
            is_superuser=self.is_superuser,
            auth_type=self.auth_type,
            workflow=workflow,
            task=task
        )
        WorkflowEventService.task_complete_event(
            task=task,
            user=self.user
        )

        if task_performer:
            if self._task_can_be_completed(task):
                self.complete_task(task=task)
                task_performers_qst.not_completed().update(
                    date_completed=timezone.now(),
                    is_completed=True
                )
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
            self.complete_task(task=task)

    def _task_is_returnable(self, task: Task):
        service = WorkflowActionService(user=self.user)
        action_method, _ = service.execute_condition(task)
        if action_method.__name__ == 'skip_task':
            if task.number == 1:
                return False
            return self._task_is_returnable(task=task.prev)
        return True

    def _return_workflow_to_task(
        self,
        workflow: Workflow,
        revert_from_task: Task,
        revert_to_task: Task,
        is_revert: bool = False
    ):

        """ Return workflow to specific task """

        with transaction.atomic():
            if is_revert:
                WorkflowEventService.task_revert_event(
                    task=revert_to_task,
                    user=self.user
                )
            else:
                WorkflowEventService.workflow_revert_event(
                    task=revert_from_task,
                    user=self.user,
                )
            next_tasks = workflow.tasks.filter(
                number__gt=revert_to_task.number
            )
            next_tasks.update(
                date_started=None,
                date_completed=None,
                is_completed=False,
                is_skipped=False
            )
            (
                TaskPerformer.objects
                .with_tasks_after(revert_to_task)
                .by_workflow(workflow.id)
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
            workflow_is_running = workflow.is_running

            # update workflow logic
            update_fields = ['current_task']
            if workflow.status == WorkflowStatus.DELAYED:
                delay = revert_from_task.get_active_delay()
                if delay:
                    delay.end_date = timezone.now()
                    if delay.directly_status:
                        delay.save(update_fields=['end_date'])
                    else:
                        revert_from_task.reset_delay(delay)
            if not workflow.is_running:
                workflow.date_completed = None
                workflow.status = WorkflowStatus.RUNNING
                update_fields.append('status')
                update_fields.append('date_completed')

            workflow.current_task -= 1

            if revert_to_task is not None:
                workflow.current_task = revert_to_task.number

            workflow.save(update_fields=update_fields)
            if workflow_is_running:
                WSSender.send_removed_task_notification(revert_from_task)

            # end update workflow logic
            action_method, by_cond = self.execute_condition(revert_to_task)
            action_method(
                workflow=workflow,
                task=revert_to_task,
                user=self.user,
                is_reverted=True,
                by_condition=by_cond,
            )

        if is_revert:
            AnalyticService.task_returned(
                user=self.user,
                task=revert_from_task,
                is_superuser=self.is_superuser,
                auth_type=self.auth_type
            )
        else:
            AnalyticService.workflow_returned(
                user=self.user,
                task=revert_to_task,
                workflow=workflow,
                is_superuser=self.is_superuser,
                auth_type=self.auth_type,
            )
        acc_id = self.user.account_id
        self._set_workflow_counts(workflow)
        if WebHook.objects.on_account(acc_id).task_returned().exists():
            send_task_returned_webhook.delay(
                user_id=self.user.id,
                account_id=acc_id,
                payload=revert_to_task.webhook_payload()
            )

    def revert(self, workflow: Workflow):

        """ Can only be applied to a running workflow """

        revert_from_task = workflow.current_task_instance
        if revert_from_task.number == 1:
            raise exceptions.FirstTaskCannotBeReverted()
        revert_to_task = revert_from_task.prev
        if workflow.is_running:
            if revert_from_task.sub_workflows.running().exists():
                raise exceptions.BlockedBySubWorkflows()
        elif workflow.is_delayed:
            raise exceptions.DelayedWorkflowCannotBeChanged()
        elif workflow.is_completed:
            raise exceptions.CompletedWorkflowCannotBeChanged()

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
        self._return_workflow_to_task(
            workflow=workflow,
            revert_from_task=revert_from_task,
            revert_to_task=revert_to_task,
            is_revert=True
        )

    def return_to(
        self,
        workflow: Workflow,
        revert_to_task: Optional[Task] = None,
    ):

        revert_from_task = workflow.current_task_instance
        if workflow.is_running:
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
        self._return_workflow_to_task(
            workflow=workflow,
            revert_from_task=revert_from_task,
            revert_to_task=revert_to_task,
        )
