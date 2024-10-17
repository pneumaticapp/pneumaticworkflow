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
    send_task_webhook,
    send_workflow_completed_webhook,
)
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


UserModel = get_user_model()


class WorkflowActionService:

    def __init__(
        self,
        user: UserModel = None,
        is_superuser: bool = False,
        auth_type: AuthTokenType = AuthTokenType.USER,
        sync: bool = False
    ):
        self.user = user
        self.is_superuser = is_superuser
        self.auth_type = auth_type
        self.sync = sync

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
            user_ids = TaskPerformer.objects.filter(
                task_id=task.id,
            ).exclude_directly_deleted().not_completed().users().user_ids()
            # notifications about event
            for user_id in user_ids:
                send_delayed_workflow_notification.delay(
                    logging=self.user.account.log_api_requests,
                    task_id=task.id,
                    author_id=self.user.id,
                    user_id=user_id,
                    account_id=self.user.account_id,
                    workflow_name=workflow.name,
                )
            # decrease tasks count
            WSSender.send_removed_task_notification(
                task=task,
                user_ids=user_ids
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

        if workflow.status == WorkflowStatus.RUNNING:
            return
        elif workflow.status in WorkflowStatus.END_STATUSES:
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

        if workflow.status == WorkflowStatus.RUNNING:
            return
        elif workflow.status in WorkflowStatus.END_STATUSES:
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
        user: Optional[UserModel],
        by_condition: bool = True,
        by_complete_task: bool = False,
        **kwargs
    ):
        """ User may be None if the external workflow ends in first step """

        user = user or workflow.account.get_owner()
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
                user=user,
            )
        elif by_complete_task:
            WorkflowEventService.workflow_complete_event(
                workflow=workflow,
                user=user
            )
            AnalyticService.workflow_completed(
                user=user,
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
                user=user,
            )
            user_ids = TaskPerformer.objects.filter(
                task_id=task.id,
            ).exclude_directly_deleted().not_completed().users().user_ids()
            WSSender.send_removed_task_notification(
                task=task,
                user_ids=user_ids
            )
        send_workflow_completed_webhook.delay(
            user_id=user.id,
            instance_id=workflow.id
        )

    def skip_task(
        self,
        workflow: Workflow,
        task: Task,
        user: UserModel,
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
        if next_task:
            action_method, _ = self.execute_condition(next_task)
            if action_method:
                action_method(
                    workflow=workflow,
                    task=next_task,
                    user=user,
                    is_reverted=is_reverted,
                )
            else:
                self.start_task(workflow=workflow, task=next_task)
        else:
            self.end_process(
                workflow=workflow,
                user=user,
                by_condition=False
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
                user=user,
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
        task_service = TaskService(
            instance=task,
            user=self.user or workflow.account.get_owner()
        )
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
        workflow.save(update_fields=('current_task',))
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

            send_task_webhook.delay(
                event_name='task_completed_v2',
                user_id=self.user.id,
                instance_id=task.id
            )
            if task.number == workflow.tasks_count:
                self.end_process(
                    workflow=workflow,
                    user=self.user,
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
