from django.contrib.auth import get_user_model
from typing import List, Optional
from pneumatic_backend.executor import RawSqlExecutor
from pneumatic_backend.accounts.queries import (
    FetchGroupTaskNotificationRecipientsQuery
)
from collections import defaultdict
from pneumatic_backend.analytics.tasks import track_group_analytics
from pneumatic_backend.analytics.events import GroupsAnalyticsEvent
from pneumatic_backend.generics.base.service import BaseModelService
from pneumatic_backend.accounts.models import UserGroup
from pneumatic_backend.processes.models import (
    TemplateOwner,
    TaskPerformer,
)
from pneumatic_backend.processes.enums import (
    OwnerType,
    PerformerType
)
from pneumatic_backend.processes.tasks.update_workflow import (
    update_workflow_owners,
)
from pneumatic_backend.notifications.tasks import (
    send_removed_task_notification,
    send_new_task_websocket
)

UserModel = get_user_model()


class UserGroupService(BaseModelService):

    def _get_template_ids(self):
        template_owner_ids = TemplateOwner.objects.filter(
            type=OwnerType.GROUP,
            group=self.instance,
            is_deleted=False
        ).values_list('template_id', flat=True)
        task_performer_template_ids = TaskPerformer.objects.filter(
            type=PerformerType.GROUP,
            group=self.instance,
            is_deleted=False
        ).exclude_directly_deleted().select_related(
            'task__workflow'
        ).values_list(
            'task__workflow__template_id', flat=True
        ).distinct()
        return list(set(template_owner_ids) | set(task_performer_template_ids))

    def _create_instance(
        self,
        name: str,
        photo: Optional[str] = '',
        users: Optional[List[int]] = None,
        **kwargs
    ):
        self.instance = UserGroup.objects.create(
            name=name,
            photo=photo,
            account=self.account,
        )
        return self.instance

    def _create_related(
        self,
        users: Optional[List[int]] = None,
        **kwargs
    ):
        if users:
            self.instance.users.set(users)

    def _create_actions(
        self,
        photo: Optional[str] = None,
        users: Optional[List[int]] = None,
        **kwargs
    ):
        track_group_analytics.delay(
            event=GroupsAnalyticsEvent.created,
            user_id=self.user.id,
            user_email=self.user.email,
            user_first_name=self.user.first_name,
            user_last_name=self.user.last_name,
            group_photo=self.instance.photo,
            group_users=users,
            account_id=self.user.account_id,
            group_id=self.instance.id,
            group_name=self.instance.name,
            auth_type=self.auth_type,
            is_superuser=self.is_superuser,
            new_users_ids=users,
            new_photo=photo
        )

    def _send_users_notification(
        self,
        user_ids: List[int],
        send_notification_task,
    ):
        query = FetchGroupTaskNotificationRecipientsQuery(
            group_id=self.instance.id,
            user_ids=user_ids,
            account_id=self.user.account_id,
        )
        recipients_query = list(RawSqlExecutor.fetch(*query.get_sql()))
        notifications = defaultdict(list)
        for recipient in recipients_query:
            notifications[recipient['task_id']].append(
                (recipient['id'], recipient['email'])
            )

        for task_id, recipients in notifications.items():
            if recipients:
                send_notification_task.delay(
                    task_id=task_id,
                    recipients=recipients,
                    account_id=self.user.account_id,
                )

    def _send_added_users_notifications(self, user_ids: List[int]):
        self._send_users_notification(
            user_ids=user_ids,
            send_notification_task=send_new_task_websocket,
        )

    def _send_removed_users_notifications(self, user_ids: List[int]):
        self._send_users_notification(
            user_ids=user_ids,
            send_notification_task=send_removed_task_notification,
        )

    def partial_update(
        self,
        force_save: bool = False,
        **update_kwargs
    ):
        users = update_kwargs.pop('users', None)
        new_name = update_kwargs.get('name')
        new_photo = update_kwargs.get('photo')
        added_users_ids = None
        removed_users_ids = None
        current_users_ids = list(
            self.instance.users.values_list('id', flat=True)
        )

        if users is not None:
            set_current_users_ids = set(current_users_ids)
            new_users_ids = set(users)
            if new_users_ids != set_current_users_ids:
                added_users_ids = list(new_users_ids - set_current_users_ids)
                removed_users_ids = list(set_current_users_ids - new_users_ids)
                if users:
                    self.instance.users.set(users)
                else:
                    self.instance.users.clear()
                template_ids = self._get_template_ids()
                if template_ids:
                    update_workflow_owners.delay(template_ids)

        if (
            added_users_ids or
            removed_users_ids or
            new_name != self.instance.name or
            new_photo != self.instance.photo
        ):
            track_group_analytics.delay(
                event=GroupsAnalyticsEvent.updated,
                user_id=self.user.id,
                user_email=self.user.email,
                user_first_name=self.user.first_name,
                user_last_name=self.user.last_name,
                group_photo=new_photo,
                group_users=users if users is not None else current_users_ids,
                account_id=self.user.account_id,
                group_id=self.instance.id,
                group_name=new_name,
                auth_type=self.auth_type,
                is_superuser=self.is_superuser,
                new_users_ids=added_users_ids,
                removed_users_ids=removed_users_ids,
                new_name=new_name if new_name != self.instance.name else None,
                new_photo=(
                    new_photo if new_photo != self.instance.photo else None
                )
            )
        result = super().partial_update(**update_kwargs, force_save=force_save)
        if added_users_ids:
            self._send_added_users_notifications(added_users_ids)
        if removed_users_ids:
            self._send_removed_users_notifications(removed_users_ids)
        return result

    def delete(self):
        template_ids = self._get_template_ids()
        users = list(self.instance.users.values_list('id', flat=True))
        track_group_analytics.delay(
            event=GroupsAnalyticsEvent.deleted,
            user_id=self.user.id,
            user_email=self.user.email,
            user_first_name=self.user.first_name,
            user_last_name=self.user.last_name,
            group_photo=self.instance.photo,
            group_users=users,
            account_id=self.user.account_id,
            group_id=self.instance.id,
            group_name=self.instance.name,
            auth_type=self.auth_type,
            is_superuser=self.is_superuser,
        )
        self.instance.delete()
        if template_ids:
            update_workflow_owners.delay(template_ids)
