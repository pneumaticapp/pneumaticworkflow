import datetime
from typing import List, Optional, Tuple

from django.db.models import Q, Count
from django.utils import timezone

from pneumatic_backend.accounts.enums import (
    UserStatus,
    LeaseLevel,
)
from pneumatic_backend.generics.querysets import (
    AccountBaseQuerySet,
    BaseQuerySet,
)
from pneumatic_backend.processes.enums import (
    DirectlyStatus
)
from pneumatic_backend.accounts.enums import (
    UserType,
    UserInviteStatus,
    NotificationStatus,
    SourceType,
)


class UserInviteQuerySet(AccountBaseQuerySet):
    def order_by_date_desc(self):
        return self.order_by('-date_created')

    def pending(self):
        return self.filter(status=UserInviteStatus.PENDING)

    def not_accepted(self):
        return self.exclude(status=UserInviteStatus.ACCEPTED)

    def not_failed(self):
        return self.exclude(status=UserInviteStatus.FAILED)

    def with_status(self, status):
        return self.filter(status=status)

    def get_invited_users_in_account(
        self,
        account_id: int,
        user_ids: Optional[List[int]] = None,
    ) -> List[int]:

        """ Returns user ids found in the list """

        queryset = self.filter(
            account_id=account_id,
            invited_user__type=UserType.USER
        ).exclude(
            invited_user__status=UserStatus.INACTIVE
        )
        if user_ids:
            queryset = queryset.filter(invited_user_id__in=user_ids)
        return queryset.only('invited_user_id').values_list(
            'invited_user_id',
            flat=True,
        )


class UserQuerySet(AccountBaseQuerySet):

    def is_comments_mentions_subscriber(self):
        return self.filter(is_comments_mentions_subscriber=True)

    def is_new_tasks_subscriber(self):
        return self.filter(is_new_tasks_subscriber=True)

    def is_complete_tasks_subscriber(self):
        return self.filter(is_complete_tasks_subscriber=True)

    def is_weekly_digest_subscriber(self, date):
        return self.filter(
            Q(is_digest_subscriber=True),
            Q(last_digest_send_time__isnull=True) |
            Q(last_digest_send_time__lt=date)
        )

    def invited(self):
        return self.filter(status=UserStatus.INVITED)

    def active(self):
        return self.filter(status=UserStatus.ACTIVE)

    def type_user(self):
        return self.filter(type=UserType.USER)

    def get_users_in_account(
        self,
        account_id: int,
        user_ids: List[int]
    ) -> List[int]:

        """ Returns user ids found in the list """

        return self.filter(
            account_id=account_id,
            id__in=user_ids
        ).only('id').values_list('id', flat=True)

    def are_users_in_account(self, account_id: int, ids: List[int]) -> bool:
        return not self.filter(~Q(account_id=account_id), id__in=ids).exists()

    def by_emails(self, email: List[str]):
        return self.filter(email__in=email)

    def account_owner(self):
        return self.filter(is_account_owner=True)

    def with_timeout_to_read_notifications(
        self,
        not_read_timeout_date: datetime.datetime
    ):
        return self.annotate(
            unread_notifications_count=Count(
                'notifications',
                Q(
                    notifications__status=NotificationStatus.NEW,
                    notifications__datetime__lt=not_read_timeout_date,
                    notifications__is_deleted=False,
                    notifications__is_notified_about_not_read=False,
                )
            )
        ).filter(unread_notifications_count__gt=0)

    def exclude_directly_deleted(self):
        return self.exclude(
            taskperformer__directly_status=DirectlyStatus.DELETED
        )

    def only_emails(self) -> list:
        return list(self.values_list('email', flat=True))

    def only_ids(self) -> Tuple[int]:
        return tuple(self.values_list('id', flat=True))

    def user_ids_set(self) -> set:
        qst = self.values_list('id', flat=True)
        return set(elem for elem in qst)


class GuestQuerySet(AccountBaseQuerySet):

    pass


class InactiveUserQuerySet(UserQuerySet):

    def type_user(self):
        return self.filter(type=UserType.USER)

    def inactive(self):
        return self.filter(status=UserStatus.INACTIVE)

    def all_account_users(self, account_id: int):

        """ Returns active, inactive and invited
            from another account users """

        in_account = Q(account_id=account_id)
        invited = (
            Q(
                incoming_invites__status__in=(
                    UserInviteStatus.NOT_FAILED_STATUSES
                ),
                incoming_invites__account_id=account_id,
                incoming_invites__is_deleted=False,
            )
        )
        return self.filter(
            (in_account | invited)
        ).distinct()


class AccountQuerySet(BaseQuerySet):

    def by_id(self, account_id):
        return self.filter(id=account_id)

    def active_template(self):
        return self.filter(
            workflows__template__is_active=True,
            workflows__template__is_deleted=False,
        )

    def only_tenants(self):
        return self.filter(lease_level=LeaseLevel.TENANT)

    def exclude_tenants(self):
        return self.exclude(lease_level=LeaseLevel.TENANT)


class AccountSystemTemplateQuerySet(BaseQuerySet):

    def template_not_added(self):
        return self.filter(is_template_added=False)

    def active(self):
        return self.filter(system_template__is_active=True)


class APIKeyQuerySet(AccountBaseQuerySet):
    pass


class NotificationsQuerySet(BaseQuerySet):
    def by_comment(self, comment_id):
        return self.filter(comment_id=comment_id)

    def by_user(self, user_id):
        return self.filter(user_id=user_id)

    def by_task(self, task_id):
        return self.filter(task_id=task_id)

    def exclude_users(self, user_ids):
        return self.filter(~Q(user_id__in=user_ids))

    def exclude_read(self):
        return self.exclude(status=NotificationStatus.READ)

    def by_ids(self, ids):
        return self.filter(id__in=ids)

    def last_created(self):
        return self.order_by('-datetime').first()

    def timeout_to_read(
        self,
        user_ids: List[int],
        not_read_timeout_date: datetime.datetime
    ):
        return self.filter(
            status=NotificationStatus.NEW,
            datetime__lt=not_read_timeout_date,
            is_notified_about_not_read=False,
            user_id__in=user_ids
        )


class SystemMessageQuerySet(BaseQuerySet):

    def new(self):
        return self.filter(
            is_delivery_completed=False,
            publication_date__lte=timezone.now(),
        )


class ContactQuerySet(BaseQuerySet):

    def active(self):
        return self.filter(status=UserStatus.ACTIVE)

    def by_user(self, user_id):
        return self.filter(user_id=user_id)

    def microsoft(self):
        return self.filter(source=SourceType.MICROSOFT)


class GroupQuerySet(AccountBaseQuerySet):

    pass
