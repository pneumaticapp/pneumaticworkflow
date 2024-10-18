import re
from typing import Optional, List, Tuple
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from pneumatic_backend.processes.models import (
    WorkflowEvent,
    Task,
    Workflow,
    Delay,
    FileAttachment,
    WorkflowEventAction,
)
from pneumatic_backend.notifications.tasks import (
    send_mention_notification,
    send_comment_notification,
    send_reaction_notification,
)
from pneumatic_backend.processes.enums import (
    WorkflowEventType,
    WorkflowEventActionType,
    CommentStatus,
    WorkflowStatus,
)
from pneumatic_backend.processes.api_v2.services.exceptions import (
    AttachmentNotFound,
    CommentTextRequired,
    CommentedWorkflowNotRunning,
    CommentIsDeleted,
)
from pneumatic_backend.processes.api_v2.serializers.workflow.events import (
    DelayEventJsonSerializer,
    TaskEventJsonSerializer
)
from pneumatic_backend.analytics.services import AnalyticService
from pneumatic_backend.generics.base.service import BaseModelService
from pneumatic_backend.notifications.tasks import send_workflow_event
from pneumatic_backend.processes.api_v2.serializers.workflow.events import (
    WorkflowEventSerializer,
)
from pneumatic_backend.services.markdown import MarkdownService


UserModel = get_user_model()


class WorkflowEventService:

    @classmethod
    def _after_create_actions(cls, event: WorkflowEvent):

        """ Send workflow event websocket """

        data = WorkflowEventSerializer(instance=event).data
        send_workflow_event.delay(data=data)

    @classmethod
    def task_complete_event(
        cls,
        user: UserModel,
        task: Task
    ) -> WorkflowEvent:

        with_attachments = task.output.with_attachments().exists()
        event = WorkflowEvent.objects.create(
            type=WorkflowEventType.TASK_COMPLETE,
            account=user.account,
            task=task,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={'event_type': WorkflowEventType.TASK_COMPLETE}
            ).data,
            with_attachments=with_attachments,
            workflow=task.workflow,
            user=user
        )
        cls._after_create_actions(event)
        return event

    @classmethod
    def task_revert_event(
        cls,
        user: UserModel,
        task: Task
    ) -> WorkflowEvent:

        event = WorkflowEvent.objects.create(
            type=WorkflowEventType.TASK_REVERT,
            account=user.account,
            task=task,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={'event_type': WorkflowEventType.TASK_REVERT}
            ).data,
            workflow=task.workflow,
            user=user
        )
        cls._after_create_actions(event)
        return event

    @classmethod
    def workflow_ended_event(
        cls,
        user: UserModel,
        workflow: Workflow
    ) -> WorkflowEvent:
        task = workflow.current_task_instance
        event = WorkflowEvent.objects.create(
            type=WorkflowEventType.ENDED,
            account=user.account,
            task=task,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={'event_type': WorkflowEventType.ENDED}
            ).data,
            workflow=workflow,
            user=user,
        )
        cls._after_create_actions(event)
        return event

    @classmethod
    def force_delay_workflow_event(
        cls,
        user: UserModel,
        workflow: Workflow,
        delay: Delay,
    ) -> WorkflowEvent:

        task = workflow.current_task_instance
        event = WorkflowEvent.objects.create(
            type=WorkflowEventType.FORCE_DELAY,
            account=user.account,
            user=user,
            workflow=workflow,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={'event_type': WorkflowEventType.FORCE_DELAY}
            ).data,
            delay_json=DelayEventJsonSerializer(delay).data,
        )
        cls._after_create_actions(event)
        return event

    @classmethod
    def force_resume_workflow_event(
        cls,
        user: UserModel,
        workflow: Workflow
    ) -> WorkflowEvent:

        task = workflow.current_task_instance
        event = WorkflowEvent.objects.create(
            type=WorkflowEventType.FORCE_RESUME,
            account=user.account,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={'event_type': WorkflowEventType.FORCE_RESUME}
            ).data,
            user=user,
            workflow=workflow,
        )
        cls._after_create_actions(event)
        return event

    @classmethod
    def workflow_revert_event(
        cls,
        user: UserModel,
        task: Task
    ) -> WorkflowEvent:

        event = WorkflowEvent.objects.create(
            account=user.account,
            type=WorkflowEventType.REVERT,
            workflow=task.workflow,
            user=user,
            task=task,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={'event_type': WorkflowEventType.REVERT}
            ).data,
        )
        cls._after_create_actions(event)
        return event

    @classmethod
    def comment_created_event(
        cls,
        user: UserModel,
        workflow: Workflow,
        text: Optional[str],
        clear_text: Optional[str] = None,
        attachments: Optional[List[int]] = None,
        after_create_actions: bool = True
    ) -> WorkflowEvent:

        task = workflow.current_task_instance
        event = WorkflowEvent.objects.create(
            account=user.account,
            type=WorkflowEventType.COMMENT,
            text=text,
            clear_text=clear_text or text,
            task=task,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={'event_type': WorkflowEventType.COMMENT}
            ).data,
            with_attachments=bool(attachments),
            workflow=workflow,
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
    ) -> WorkflowEvent:

        task = workflow.current_task_instance
        event = WorkflowEvent.objects.create(
            type=event_type,
            account=user.account,
            task=task,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={'event_type': event_type}
            ).data,
            workflow=workflow,
            user=user,
        )
        cls._after_create_actions(event)
        return event

    @classmethod
    def performer_created_event(
        cls,
        user: UserModel,
        task: Task,
        performer: UserModel,
    ) -> WorkflowEvent:

        event = WorkflowEvent.objects.create(
            type=WorkflowEventType.TASK_PERFORMER_CREATED,
            account=user.account,
            task=task,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={
                    'event_type': WorkflowEventType.TASK_PERFORMER_CREATED
                }
            ).data,
            workflow=task.workflow,
            user=user,
            target_user_id=performer.id,
        )
        cls._after_create_actions(event)
        return event

    @classmethod
    def performer_deleted_event(
        cls,
        user: UserModel,
        task: Task,
        performer: UserModel,
    ) -> WorkflowEvent:

        event = WorkflowEvent.objects.create(
            type=WorkflowEventType.TASK_PERFORMER_DELETED,
            account=user.account,
            task=task,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={
                    'event_type': WorkflowEventType.TASK_PERFORMER_DELETED
                }
            ).data,
            workflow=task.workflow,
            user=user,
            target_user_id=performer.id,
        )
        cls._after_create_actions(event)
        return event

    @classmethod
    def due_date_changed_event(
        cls,
        user: UserModel,
        task: Task
    ) -> WorkflowEvent:

        event = WorkflowEvent.objects.create(
            type=WorkflowEventType.DUE_DATE_CHANGED,
            account=user.account,
            workflow=task.workflow,
            user=user,
            task=task,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={'event_type': WorkflowEventType.DUE_DATE_CHANGED}
            ).data,
        )
        cls._after_create_actions(event)
        return event

    @classmethod
    def task_skip_event(cls, task: Task) -> WorkflowEvent:

        event = WorkflowEvent.objects.create(
            type=WorkflowEventType.TASK_SKIP,
            account=task.account,
            workflow=task.workflow,
            task=task,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={'event_type': WorkflowEventType.TASK_SKIP}
            ).data,
        )
        cls._after_create_actions(event)
        return event

    @classmethod
    def workflow_run_event(
        cls,
        workflow: Workflow,
        user: Optional[UserModel] = None,
    ) -> WorkflowEvent:

        task = workflow.current_task_instance
        return WorkflowEvent.objects.create(
            type=WorkflowEventType.RUN,
            account=workflow.account,
            workflow=workflow,
            user=user,  # For highlights
            task=task,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={'event_type': WorkflowEventType.RUN}
            ).data,
        )

    @classmethod
    def sub_workflow_run_event(
        cls,
        workflow: Workflow,
        sub_workflow: Workflow,
        user: UserModel,
        after_create_actions: bool = True
    ) -> WorkflowEvent:

        task = workflow.current_task_instance
        event = WorkflowEvent.objects.create(
            type=WorkflowEventType.SUB_WORKFLOW_RUN,
            account=workflow.account,
            workflow=workflow,
            user=user,  # For highlights
            task=task,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={
                    'event_type': WorkflowEventType.SUB_WORKFLOW_RUN,
                    'sub_workflow': sub_workflow
                }
            ).data,
        )
        if after_create_actions:
            cls._after_create_actions(event)
        return event

    @classmethod
    def workflow_complete_event(
        cls,
        workflow: Workflow,
        user: Optional[UserModel] = None,
    ) -> WorkflowEvent:

        task = workflow.current_task_instance
        event = WorkflowEvent.objects.create(
            type=WorkflowEventType.COMPLETE,
            account=workflow.account,
            task=task,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={'event_type': WorkflowEventType.COMPLETE}
            ).data,
            workflow=workflow,
            user=user,  # For highlights
        )
        cls._after_create_actions(event)
        return event

    @classmethod
    def workflow_ended_by_condition_event(
        cls,
        workflow: Workflow,
        user: Optional[UserModel] = None,
    ) -> WorkflowEvent:

        task = workflow.current_task_instance
        event = WorkflowEvent.objects.create(
            type=WorkflowEventType.ENDED_BY_CONDITION,
            account=workflow.account,
            task=task,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={'event_type': WorkflowEventType.ENDED_BY_CONDITION}
            ).data,
            workflow=workflow,
            user=user,  # Only for highlights
        )
        cls._after_create_actions(event)
        return event

    @classmethod
    def workflow_delay_event(
        cls,
        workflow: Workflow,
        delay: Delay
    ) -> WorkflowEvent:

        task = workflow.current_task_instance
        event = WorkflowEvent.objects.create(
            type=WorkflowEventType.DELAY,
            account=workflow.account,
            task=task,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={'event_type': WorkflowEventType.DELAY}
            ).data,
            workflow=workflow,
            delay_json=DelayEventJsonSerializer(delay).data,
        )
        cls._after_create_actions(event)
        return event

    @classmethod
    def task_started_event(cls, task: Task) -> WorkflowEvent:

        event = WorkflowEvent.objects.create(
            type=WorkflowEventType.TASK_START,
            account=task.account,
            task=task,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={'event_type': WorkflowEventType.TASK_START}
            ).data,
            workflow=task.workflow,
        )
        cls._after_create_actions(event)
        return event

    @classmethod
    def task_skip_no_performers_event(cls, task: Task) -> WorkflowEvent:

        event = WorkflowEvent.objects.create(
            type=WorkflowEventType.TASK_SKIP_NO_PERFORMERS,
            account=task.account,
            workflow=task.workflow,
            task=task,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={
                    'event_type': WorkflowEventType.TASK_SKIP_NO_PERFORMERS
                }
            ).data,
        )
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

        list_of_ids = re.findall(r'\[[\w\s\']+\|([0-9]+)\]', text)
        if not list_of_ids:
            return tuple()
        return UserModel.objects.filter(
            id__in=list_of_ids
        ).exclude(id__in=exclude_ids).on_account(
            self.account.id
        ).only_ids()

    def _update_attachments(self, ids: Optional[List[int]] = None):

        """ Attach new attachments to comment event and remove previous """

        if ids:
            self.instance.attachments.exclude(id__in=ids).delete()
            qst = FileAttachment.objects.on_account(
                self.account.id
            ).with_event_or_not_attached(self.instance.id).by_ids(ids)

            if qst.count() < len(ids):
                raise AttachmentNotFound()
            qst.update(
                event=self.instance,
                workflow=self.instance.workflow
            )
        else:
            self.instance.attachments.all().delete()

    def _get_new_comment_recipients(self) -> Tuple[Tuple[int], Tuple[int]]:

        """ Return mentioned users and comment notification receipenes """

        workflow = self.instance.workflow
        task = workflow.current_task_instance
        mentioned_users_ids = tuple()
        notify_users_ids = task.taskperformer_set.exclude_directly_deleted(
        ).exclude(user_id=self.user.id).user_ids()
        if self.instance.text:
            mentioned_users_ids = self._get_mentioned_users_ids(
                text=self.instance.text,
                exclude_ids=notify_users_ids
            )
        notify_users_ids = tuple(
            set(notify_users_ids) - set(mentioned_users_ids)
        )
        return mentioned_users_ids, notify_users_ids

    def _get_updated_comment_recipients(self) -> Tuple[int]:

        """ Return only new mentioned users """

        workflow = self.instance.workflow
        mentioned_users_ids = tuple()
        if self.instance.text:
            # Only new mentioned users
            mentioned_users_ids = self._get_mentioned_users_ids(
                text=self.instance.text,
                exclude_ids=workflow.members.values_list('id', flat=True)
            )
        return mentioned_users_ids

    def _send_workflow_event(self):
        data = WorkflowEventSerializer(instance=self.instance).data
        send_workflow_event.delay(data=data)

    def _validate_comment_action(self):
        if self.instance.status == CommentStatus.DELETED:
            raise CommentIsDeleted()
        if self.instance.workflow.status in WorkflowStatus.END_STATUSES:
            raise CommentedWorkflowNotRunning()

    def create(
        self,
        workflow: Workflow,
        text: Optional[str] = None,
        attachments: Optional[List[int]] = None,
    ) -> WorkflowEvent:

        """ If the user is a performer and is mentioned in the message,
            then only a notification about a new comment
            will be sent to him """

        if workflow.status in WorkflowStatus.END_STATUSES:
            raise CommentedWorkflowNotRunning()
        if not text and not attachments:
            raise CommentTextRequired()
        clear_text = MarkdownService.clear(text) if text else None
        with transaction.atomic():
            self.instance = WorkflowEventService.comment_created_event(
                user=self.user,
                workflow=workflow,
                text=text,
                clear_text=clear_text,
                attachments=attachments
            )
            task = workflow.current_task_instance
            if not task.contains_comments:
                task.contains_comments = True
                task.save(update_fields=['contains_comments'])
            if attachments:
                self._update_attachments(attachments)
            mentioned_users_ids, notify_users_ids = (
                self._get_new_comment_recipients()
            )
            if mentioned_users_ids:
                workflow.members.add(*mentioned_users_ids)
                send_mention_notification.delay(
                    logging=self.user.account.log_api_requests,
                    author_id=self.user.id,
                    task_id=task.id,
                    account_id=self.user.account.id,
                    users_ids=mentioned_users_ids,
                    text=self.instance.text
                )
                AnalyticService.mentions_created(
                    user=self.user,
                    is_superuser=self.is_superuser,
                    auth_type=self.auth_type,
                    workflow=workflow
                )
            if notify_users_ids:
                send_comment_notification.delay(
                    logging=self.account.log_api_requests,
                    author_id=self.user.id,
                    task_id=task.id,
                    account_id=self.account.id,
                    users_ids=notify_users_ids,
                    text=self.instance.text
                )
                AnalyticService.comment_added(
                    user=self.user,
                    is_superuser=self.is_superuser,
                    auth_type=self.auth_type,
                    workflow=workflow
                )
            return self.instance

    def update(
        self,
        force_save=False,
        **update_kwargs,
    ) -> WorkflowEvent:

        self._validate_comment_action()
        if (
            not update_kwargs.get('text', self.instance.text)
            and not update_kwargs.get(
                'attachments',
                self.instance.with_attachments
            )
        ):
            raise CommentTextRequired()

        kwargs = {
            'status': CommentStatus.UPDATED,
            'updated': timezone.now(),
        }
        if 'text' in update_kwargs:
            kwargs['text'] = update_kwargs['text']
            if update_kwargs['text']:
                kwargs['clear_text'] = MarkdownService.clear(
                    update_kwargs['text']
                )
            else:
                kwargs['clear_text'] = None
        if 'attachments' in update_kwargs:
            kwargs['with_attachments'] = True

        with transaction.atomic():
            self.instance = self.partial_update(
                force_save=force_save,
                **kwargs
            )
            if 'attachments' in update_kwargs:
                self._update_attachments(update_kwargs['attachments'])
            new_mentioned_users_ids = self._get_updated_comment_recipients()
            if new_mentioned_users_ids:
                self.instance.workflow.members.add(*new_mentioned_users_ids)
                send_mention_notification.delay(
                    logging=self.user.account.log_api_requests,
                    author_id=self.user.id,
                    task_id=self.instance.task.id,
                    account_id=self.user.account.id,
                    users_ids=new_mentioned_users_ids,
                    text=self.instance.text
                )

        self._send_workflow_event()
        AnalyticService.comment_edited(
            user=self.user,
            is_superuser=self.is_superuser,
            auth_type=self.auth_type,
            workflow=self.instance.workflow
        )

        return self.instance

    def delete(self):

        self._validate_comment_action()
        self.instance.attachments.delete()
        super().partial_update(
            status=CommentStatus.DELETED,
            with_attachments=False,
            text=None,
            force_save=True,
        )
        self._send_workflow_event()
        AnalyticService.comment_deleted(
            user=self.user,
            is_superuser=self.is_superuser,
            auth_type=self.auth_type,
            workflow=self.instance.workflow
        )
        return self.instance

    def watched(self):

        """ The value is not entered directly to avoid concurrent entry """

        self._validate_comment_action()
        if not self.user == self.instance.user:
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
                force_save=True
            )
            AnalyticService.comment_reaction_added(
                user=self.user,
                workflow=self.instance.workflow,
                is_superuser=self.is_superuser,
                auth_type=self.auth_type
            )
            self._send_workflow_event()
            # Don't send reactions to yourself
            if self.user.id != self.instance.user_id:
                send_reaction_notification.delay(
                    logging=self.account.log_api_requests,
                    author_id=self.user.id,
                    author_name=self.user.name,
                    task_id=self.instance.task_id,
                    account_id=self.account.id,
                    user_id=self.instance.user_id,
                    reaction=value,
                    workflow_name=self.instance.workflow.name,
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
                force_save=True
            )
            AnalyticService.comment_reaction_deleted(
                user=self.user,
                workflow=self.instance.workflow,
                is_superuser=self.is_superuser,
                auth_type=self.auth_type
            )
            self._send_workflow_event()
