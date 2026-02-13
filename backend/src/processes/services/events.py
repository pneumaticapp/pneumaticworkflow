import re
from typing import List, Optional, Tuple

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from src.accounts.models import UserGroup
from src.analysis.services import AnalyticService
from src.generics.base.service import BaseModelService
from src.notifications.tasks import (
    send_comment_notification,
    send_mention_notification,
    send_reaction_notification,
    send_workflow_event,
)
from src.processes.enums import (
    CommentStatus,
    WorkflowEventActionType,
    WorkflowEventType,
)
from src.processes.models.workflows.event import (
    WorkflowEvent,
    WorkflowEventAction,
)
from src.processes.models.workflows.task import (
    Delay,
    Task,
)
from src.processes.models.workflows.workflow import Workflow
from src.processes.serializers.workflows.events import (
    DelayEventJsonSerializer,
    TaskEventJsonSerializer,
    WorkflowEventSerializer,
)
from src.processes.services.exceptions import (
    CommentedNotTask,
    CommentedTaskNotActive,
    CommentedWorkflowNotRunning,
    CommentIsDeleted,
    CommentTextRequired,
)
from src.services.markdown import MarkdownService
from src.storage.utils import refresh_attachments

UserModel = get_user_model()


class WorkflowEventService:

    @classmethod
    def _after_create_actions(cls, event: WorkflowEvent):

        """ Send workflow event websocket """

        data = WorkflowEventSerializer(instance=event).data
        send_workflow_event.delay(
            logging=event.account.log_api_requests,
            logo_lg=event.account.logo_lg,
            account_id=event.account_id,
            data=data,
        )

    @classmethod
    def task_complete_event(
        cls,
        user: UserModel,
        task: Task,
        after_create_actions: bool = True,
    ) -> WorkflowEvent:

        with_attachments = task.output.with_attachments().exists()
        event = WorkflowEvent.objects.create(
            type=WorkflowEventType.TASK_COMPLETE,
            account=user.account,
            task=task,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={'event_type': WorkflowEventType.TASK_COMPLETE},
            ).data,
            with_attachments=with_attachments,
            workflow=task.workflow,
            user=user,
        )
        if after_create_actions:
            cls._after_create_actions(event)
        return event

    @classmethod
    def task_revert_event(
        cls,
        user: UserModel,
        task: Task,
        text: str,
        clear_text: str,
        after_create_actions: bool = True,
    ) -> WorkflowEvent:

        event = WorkflowEvent.objects.create(
            type=WorkflowEventType.TASK_REVERT,
            text=text,
            clear_text=clear_text or text,
            account=user.account,
            task=task,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={'event_type': WorkflowEventType.TASK_REVERT},
            ).data,
            workflow=task.workflow,
            user=user,
        )
        if after_create_actions:
            cls._after_create_actions(event)
        return event

    @classmethod
    def task_delay_event(
        cls,
        user: UserModel,
        task: Task,
        delay: Delay,
        after_create_actions: bool = True,
    ) -> WorkflowEvent:

        event = WorkflowEvent.objects.create(
            type=WorkflowEventType.TASK_DELAY,
            account=user.account,
            task=task,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={'event_type': WorkflowEventType.TASK_DELAY},
            ).data,
            workflow=task.workflow,
            delay_json=DelayEventJsonSerializer(delay).data,
        )
        if after_create_actions:
            cls._after_create_actions(event)
        return event

    @classmethod
    def workflow_ended_event(
        cls,
        user: UserModel,
        workflow: Workflow,
        after_create_actions: bool = True,
    ) -> WorkflowEvent:

        event = WorkflowEvent.objects.create(
            type=WorkflowEventType.ENDED,
            account=user.account,
            workflow=workflow,
            user=user,
        )
        if after_create_actions:
            cls._after_create_actions(event)
        return event

    @classmethod
    def force_delay_workflow_event(
        cls,
        user: UserModel,
        workflow: Workflow,
        delay: Delay,
        after_create_actions: bool = True,
    ) -> WorkflowEvent:

        event = WorkflowEvent.objects.create(
            type=WorkflowEventType.FORCE_DELAY,
            account=user.account,
            user=user,
            workflow=workflow,
            delay_json=DelayEventJsonSerializer(delay).data,
        )
        if after_create_actions:
            cls._after_create_actions(event)
        return event

    @classmethod
    def force_resume_workflow_event(
        cls,
        user: UserModel,
        workflow: Workflow,
        after_create_actions: bool = True,
    ) -> WorkflowEvent:

        event = WorkflowEvent.objects.create(
            type=WorkflowEventType.FORCE_RESUME,
            account=user.account,
            user=user,
            workflow=workflow,
        )
        if after_create_actions:
            cls._after_create_actions(event)
        return event

    @classmethod
    def workflow_revert_event(
        cls,
        user: UserModel,
        task: Task,
        after_create_actions: bool = True,
    ) -> WorkflowEvent:

        event = WorkflowEvent.objects.create(
            account=user.account,
            type=WorkflowEventType.REVERT,
            workflow=task.workflow,
            user=user,
            task=task,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={'event_type': WorkflowEventType.REVERT},
            ).data,
        )
        if after_create_actions:
            cls._after_create_actions(event)
        return event

    @classmethod
    def comment_created_event(
        cls,
        user: UserModel,
        task: Task,
        text: Optional[str],
        clear_text: Optional[str] = None,
        after_create_actions: bool = True,
    ) -> WorkflowEvent:

        event = WorkflowEvent.objects.create(
            account=user.account,
            type=WorkflowEventType.COMMENT,
            text=text,
            clear_text=clear_text or text,
            task=task,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={'event_type': WorkflowEventType.COMMENT},
            ).data,
            with_attachments=False,  # Will be updated by refresh_attachments
            workflow=task.workflow,
            user=user,
        )
        if after_create_actions:
            cls._after_create_actions(event)
        return event

    @classmethod
    def workflow_urgent_event(
        cls,
        user: UserModel,
        event_type: WorkflowEventType.URGENT_TYPES,
        workflow: Workflow,
        after_create_actions: bool = True,
    ) -> WorkflowEvent:

        event = WorkflowEvent.objects.create(
            type=event_type,
            account=user.account,
            workflow=workflow,
            user=user,
        )
        if after_create_actions:
            cls._after_create_actions(event)
        return event

    @classmethod
    def performer_created_event(
        cls,
        user: UserModel,
        task: Task,
        performer: UserModel,
        after_create_actions: bool = True,
    ) -> WorkflowEvent:

        event = WorkflowEvent.objects.create(
            type=WorkflowEventType.TASK_PERFORMER_CREATED,
            account=user.account,
            task=task,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={
                    'event_type': WorkflowEventType.TASK_PERFORMER_CREATED,
                },
            ).data,
            workflow=task.workflow,
            user=user,
            target_user_id=performer.id,
        )
        if after_create_actions:
            cls._after_create_actions(event)
        return event

    @classmethod
    def performer_group_created_event(
        cls,
        user: UserModel,
        task: Task,
        performer: UserGroup,
        after_create_actions: bool = True,
    ) -> WorkflowEvent:

        event = WorkflowEvent.objects.create(
            type=WorkflowEventType.TASK_PERFORMER_GROUP_CREATED,
            account=user.account,
            task=task,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={
                    'event_type':
                        WorkflowEventType.TASK_PERFORMER_GROUP_CREATED,
                },
            ).data,
            workflow=task.workflow,
            user=user,
            target_group_id=performer.id,
        )
        if after_create_actions:
            cls._after_create_actions(event)
        return event

    @classmethod
    def performer_deleted_event(
        cls,
        user: UserModel,
        task: Task,
        performer: UserModel,
        after_create_actions: bool = True,
    ) -> WorkflowEvent:

        event = WorkflowEvent.objects.create(
            type=WorkflowEventType.TASK_PERFORMER_DELETED,
            account=user.account,
            task=task,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={
                    'event_type': WorkflowEventType.TASK_PERFORMER_DELETED,
                },
            ).data,
            workflow=task.workflow,
            user=user,
            target_user_id=performer.id,
        )
        if after_create_actions:
            cls._after_create_actions(event)
        return event

    @classmethod
    def performer_group_deleted_event(
        cls,
        user: UserModel,
        task: Task,
        performer: UserGroup,
        after_create_actions: bool = True,
    ) -> WorkflowEvent:

        event = WorkflowEvent.objects.create(
            type=WorkflowEventType.TASK_PERFORMER_GROUP_DELETED,
            account=user.account,
            task=task,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={
                    'event_type':
                        WorkflowEventType.TASK_PERFORMER_GROUP_DELETED,
                },
            ).data,
            workflow=task.workflow,
            user=user,
            target_group_id=performer.id,
        )
        if after_create_actions:
            cls._after_create_actions(event)
        return event

    @classmethod
    def due_date_changed_event(
        cls,
        user: UserModel,
        task: Task,
        after_create_actions: bool = True,
    ) -> WorkflowEvent:

        event = WorkflowEvent.objects.create(
            type=WorkflowEventType.DUE_DATE_CHANGED,
            account=user.account,
            workflow=task.workflow,
            user=user,
            task=task,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={'event_type': WorkflowEventType.DUE_DATE_CHANGED},
            ).data,
        )
        if after_create_actions:
            cls._after_create_actions(event)
        return event

    @classmethod
    def task_skip_event(
        cls,
        task: Task,
        after_create_actions: bool = True,
    ) -> WorkflowEvent:

        event = WorkflowEvent.objects.create(
            type=WorkflowEventType.TASK_SKIP,
            account=task.account,
            workflow=task.workflow,
            task=task,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={'event_type': WorkflowEventType.TASK_SKIP},
            ).data,
        )
        if after_create_actions:
            cls._after_create_actions(event)
        return event

    @classmethod
    def workflow_run_event(
        cls,
        workflow: Workflow,
        user: Optional[UserModel] = None,
    ) -> WorkflowEvent:

        return WorkflowEvent.objects.create(
            type=WorkflowEventType.RUN,
            account=workflow.account,
            workflow=workflow,
            user=user,  # For highlights
        )

    @classmethod
    def sub_workflow_run_event(
        cls,
        workflow: Workflow,
        sub_workflow: Workflow,
        user: UserModel,
        after_create_actions: bool = True,
    ) -> WorkflowEvent:

        event = WorkflowEvent.objects.create(
            type=WorkflowEventType.SUB_WORKFLOW_RUN,
            account=workflow.account,
            workflow=workflow,
            user=user,  # For highlights
            task=sub_workflow.ancestor_task,
            task_json=TaskEventJsonSerializer(
                instance=sub_workflow.ancestor_task,
                context={
                    'event_type': WorkflowEventType.SUB_WORKFLOW_RUN,
                    'sub_workflow': sub_workflow,
                },
            ).data,
        )
        if after_create_actions:
            cls._after_create_actions(event)
        return event

    @classmethod
    def workflow_complete_event(
        cls,
        workflow: Workflow,
        task: Task,
        user: Optional[UserModel] = None,
        after_create_actions: bool = True,
    ) -> WorkflowEvent:

        event = WorkflowEvent.objects.create(
            type=WorkflowEventType.COMPLETE,
            account=workflow.account,
            task=task,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={'event_type': WorkflowEventType.COMPLETE},
            ).data,
            workflow=workflow,
            user=user,  # For highlights
        )
        if after_create_actions:
            cls._after_create_actions(event)
        return event

    @classmethod
    def workflow_ended_by_condition_event(
        cls,
        workflow: Workflow,
        task: Task,
        user: Optional[UserModel] = None,
        after_create_actions: bool = True,
    ) -> WorkflowEvent:

        event = WorkflowEvent.objects.create(
            type=WorkflowEventType.ENDED_BY_CONDITION,
            account=workflow.account,
            task=task,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={'event_type': WorkflowEventType.ENDED_BY_CONDITION},
            ).data,
            workflow=workflow,
            user=user,  # Only for highlights
        )
        if after_create_actions:
            cls._after_create_actions(event)
        return event

    @classmethod
    def workflow_delay_event(
        cls,
        workflow: Workflow,
        delay: Delay,
        after_create_actions: bool = True,
    ) -> WorkflowEvent:

        event = WorkflowEvent.objects.create(
            type=WorkflowEventType.DELAY,
            account=workflow.account,
            workflow=workflow,
            delay_json=DelayEventJsonSerializer(delay).data,
        )
        if after_create_actions:
            cls._after_create_actions(event)
        return event

    @classmethod
    def task_started_event(
        cls,
        task: Task,
        after_create_actions: bool = True,
    ) -> WorkflowEvent:

        event = WorkflowEvent.objects.create(
            type=WorkflowEventType.TASK_START,
            account=task.account,
            task=task,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={'event_type': WorkflowEventType.TASK_START},
            ).data,
            workflow=task.workflow,
        )
        if after_create_actions:
            cls._after_create_actions(event)
        return event

    @classmethod
    def task_skip_no_performers_event(
        cls,
        task: Task,
        after_create_actions: bool = True,
    ) -> WorkflowEvent:

        event = WorkflowEvent.objects.create(
            type=WorkflowEventType.TASK_SKIP_NO_PERFORMERS,
            account=task.account,
            workflow=task.workflow,
            task=task,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={
                    'event_type': WorkflowEventType.TASK_SKIP_NO_PERFORMERS,
                },
            ).data,
        )
        if after_create_actions:
            cls._after_create_actions(event)
        return event


class CommentService(BaseModelService):

    def _create_related(self, **kwargs):
        pass

    def _create_instance(self, **kwargs):
        pass

    def _get_mentioned_users_ids(
        self,
        text: str,
        exclude_ids: List[int],
    ) -> Tuple[int]:
        list_of_ids = re.findall(r'\[.*?\|\s*([0-9]+)\]', text)
        if not list_of_ids:
            return ()
        return UserModel.objects.filter(
            id__in=list_of_ids,
        ).exclude(id__in=exclude_ids).on_account(
            self.account.id,
        ).only_ids()

    def _get_new_comment_recipients(
        self,
        task: Task,
    ) -> Tuple[Tuple[int], Tuple[int]]:

        """ Return mentioned users and comment notification receipenes """

        mentioned_users_ids = ()
        notify_users_ids = task.taskperformer_set.exclude_directly_deleted(
        ).exclude(user_id=self.user.id).user_ids()
        if self.instance.text:
            mentioned_users_ids = self._get_mentioned_users_ids(
                text=self.instance.text,
                exclude_ids=notify_users_ids,
            )
        notify_users_ids = tuple(
            set(notify_users_ids) - set(mentioned_users_ids),
        )
        return mentioned_users_ids, notify_users_ids

    def _get_updated_comment_recipients(self) -> Tuple[int]:

        """ Return only new mentioned users """

        workflow = self.instance.workflow
        mentioned_users_ids = ()
        if self.instance.text:
            # Only new mentioned users
            mentioned_users_ids = self._get_mentioned_users_ids(
                text=self.instance.text,
                exclude_ids=workflow.members.values_list('id', flat=True),
            )
        return mentioned_users_ids

    def _send_workflow_event(self):
        data = WorkflowEventSerializer(instance=self.instance).data
        send_workflow_event.delay(
            logging=self.instance.account.log_api_requests,
            logo_lg=self.instance.account.logo_lg,
            account_id=self.instance.account_id,
            data=data,
        )

    def _validate_comment_action(self):
        if self.instance.status == CommentStatus.DELETED:
            raise CommentIsDeleted
        if self.instance.workflow.is_completed:
            raise CommentedWorkflowNotRunning

    def create(
        self,
        task: Task,
        text: Optional[str] = None,
    ) -> WorkflowEvent:

        """ If the user is a performer and is mentioned in the message,
            then only a notification about a new comment
            will be sent to him """
        if task is None:
            raise CommentedNotTask
        if not (task.is_active or task.is_delayed):
            raise CommentedTaskNotActive
        workflow = task.workflow
        if workflow.is_completed:
            raise CommentedWorkflowNotRunning
        if not text:
            raise CommentTextRequired
        clear_text = MarkdownService.clear(text) if text else None
        with transaction.atomic():
            self.instance = WorkflowEventService.comment_created_event(
                user=self.user,
                task=task,
                text=text,
                clear_text=clear_text,
                after_create_actions=False,
            )
            if not task.contains_comments:
                task.contains_comments = True
                task.save(update_fields=['contains_comments'])
            refresh_attachments(source=self.instance, user=self.user)
            WorkflowEventService._after_create_actions(self.instance)
            mentioned_users_ids, notify_users_ids = (
                self._get_new_comment_recipients(task)
            )
            if mentioned_users_ids:
                workflow.members.add(*mentioned_users_ids)
                send_mention_notification.delay(
                    logging=self.user.account.log_api_requests,
                    logo_lg=self.user.account.logo_lg,
                    author_id=self.user.id,
                    event_id=self.instance.id,
                    account_id=self.user.account.id,
                    users_ids=mentioned_users_ids,
                    text=self.instance.text,
                )
                AnalyticService.mentions_created(
                    text=clear_text,
                    user=self.user,
                    is_superuser=self.is_superuser,
                    auth_type=self.auth_type,
                    workflow=workflow,
                )
            if notify_users_ids:
                send_comment_notification.delay(
                    logging=self.account.log_api_requests,
                    logo_lg=self.account.logo_lg,
                    author_id=self.user.id,
                    event_id=self.instance.id,
                    account_id=self.account.id,
                    users_ids=notify_users_ids,
                    text=self.instance.text,
                )
                AnalyticService.comment_added(
                    text=clear_text,
                    user=self.user,
                    is_superuser=self.is_superuser,
                    auth_type=self.auth_type,
                    workflow=workflow,
                )
            return self.instance

    def update(
        self,
        force_save=False,
        text: Optional[str] = None,
    ) -> WorkflowEvent:

        self._validate_comment_action()
        task = self.instance.task
        if task is not None and not (task.is_active or task.is_delayed):
            raise CommentedTaskNotActive
        if not text:
            raise CommentTextRequired
        clear_text = MarkdownService.clear(text) if text else None
        kwargs = {
            'status': CommentStatus.UPDATED,
            'updated': timezone.now(),
            'text': text,
            'clear_text': clear_text,
        }

        with transaction.atomic():
            self.instance = self.partial_update(
                force_save=force_save,
                **kwargs,
            )
            refresh_attachments(source=self.instance, user=self.user)
            new_mentioned_users_ids = self._get_updated_comment_recipients()
            if new_mentioned_users_ids:
                self.instance.workflow.members.add(*new_mentioned_users_ids)
                send_mention_notification.delay(
                    logging=self.user.account.log_api_requests,
                    logo_lg=self.user.account.logo_lg,
                    author_id=self.user.id,
                    event_id=self.instance.id,
                    account_id=self.user.account.id,
                    users_ids=new_mentioned_users_ids,
                    text=self.instance.text,
                )

        self._send_workflow_event()
        AnalyticService.comment_edited(
            text=clear_text,
            user=self.user,
            is_superuser=self.is_superuser,
            auth_type=self.auth_type,
            workflow=self.instance.workflow,
        )

        return self.instance

    def delete(self):

        self._validate_comment_action()
        task = self.instance.task
        if task is not None and not (task.is_active or task.is_delayed):
            raise CommentedTaskNotActive
        self.instance.storage_attachments.delete()
        super().partial_update(
            status=CommentStatus.DELETED,
            with_attachments=False,
            text=None,
            force_save=True,
        )
        self._send_workflow_event()
        AnalyticService.comment_deleted(
            text=self.instance.clear_text,
            user=self.user,
            is_superuser=self.is_superuser,
            auth_type=self.auth_type,
            workflow=self.instance.workflow,
        )
        return self.instance

    def watched(self):

        """ The value is not entered directly to avoid concurrent entry """

        self._validate_comment_action()
        if self.user != self.instance.user:
            watched = {el['user_id'] for el in self.instance.watched}
            if self.user.id not in watched:
                WorkflowEventAction.objects.get_or_create(
                    event=self.instance,
                    user=self.user,
                    type=WorkflowEventActionType.WATCHED,
                 )

    def create_reaction(self, value: str):

        self._validate_comment_action()
        try:
            already = self.user.id in self.instance.reactions[value]
            if not already:
                raise KeyError('=(')
        except KeyError:
            self.instance.reactions.setdefault(value, []).append(self.user.id)
            self.partial_update(
                reactions=self.instance.reactions,
                force_save=True,
            )
            AnalyticService.comment_reaction_added(
                text=value,
                user=self.user,
                workflow=self.instance.workflow,
                is_superuser=self.is_superuser,
                auth_type=self.auth_type,
            )
            self._send_workflow_event()
            # Don't send reactions to yourself
            if self.user.id != self.instance.user_id:
                send_reaction_notification.delay(
                    logging=self.account.log_api_requests,
                    account_id=self.account.id,
                    logo_lg=self.account.logo_lg,
                    author_id=self.user.id,
                    author_name=self.user.name,
                    event_id=self.instance.id,
                    user_id=self.instance.user_id,
                    user_email=self.instance.user.email,
                    reaction=value,
                )

    def delete_reaction(self, value: str):

        self._validate_comment_action()
        try:
            self.instance.reactions[value].remove(self.user.id)
        except (KeyError, ValueError):
            # Already deleted
            pass
        else:
            if not self.instance.reactions[value]:
                self.instance.reactions.pop(value)
            self.partial_update(
                reactions=self.instance.reactions,
                force_save=True,
            )
            AnalyticService.comment_reaction_deleted(
                text=value,
                user=self.user,
                workflow=self.instance.workflow,
                is_superuser=self.is_superuser,
                auth_type=self.auth_type,
            )
            self._send_workflow_event()
