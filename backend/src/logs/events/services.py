import logging
from datetime import date, datetime
from time import monotonic
from typing import Any, Callable, Dict, List, Optional, Union

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.functional import SimpleLazyObject

from src.authentication.enums import AuthTokenType
from src.logs.events.entities import (
    Actor,
    Event,
    EventObject,
    RequestContext,
    request_context,
)
from src.logs.events.enums import (
    AccountEvents,
    AdminEvents,
    ApiKeyEvents,
    BillingEvents,
    DatasetEvents,
    EventCategory,
    GroupEvents,
    LoginFailedReason,
    LogoutReason,
    TaskEvents,
    TemplateEvents,
    UserEvents,
    WebhookEvents,
    WorkflowEvents,
)
from src.logs.events.schema import (
    PAYLOAD_STR_MAX,
    normalize_payload,
    without_url_secrets,
)
from src.logs.events.stream import get_stream
from src.utils.logging import capture_sentry_message_throttled

logger = logging.getLogger('pneumatic.events')
NO_ACCOUNT = 0
CIRCUIT_OPEN_SECONDS = 15.0


class AuditEventService:
    """Audit events of user actions. Public methods choose the category,
    tenant and payload; _event builds and schedules the record.
    Model types are documented without importing other apps.
    """

    _circuit_open_until: float = 0.0
    _dropped: int = 0

    @classmethod
    def _event(
        cls,
        *,
        event_category: str,
        event_type: str,
        user,
        auth_type: Optional[str],
        account_id: Union[int, Callable[[], int]],
        object_id: Optional[Union[int, str, Callable[[], int]]] = None,
        payload: Optional[
            Union[Dict[str, Any], Callable[[], Dict[str, Any]]]
        ] = None,
        workflow_id: Optional[Union[int, Callable[[], int]]] = None,
        task_id: Optional[Union[int, Callable[[], int]]] = None,
        object_name: Optional[Union[str, Callable[[], str]]] = None,
        account_name: Optional[Union[str, Callable[[], Optional[str]]]] = None,
    ):
        """Build an event and write it after commit.

        user: accounts.User or None for a system action.
        account_id: The tenant chosen by the public action method.
        An unset backend disables the journal; the configuration of an
        enabled one is validated once at startup (LogsConfig.ready).
        Callables defer related identifiers, names and payloads until enabled.
        Resolve them now, so the record is a snapshot before commit.
        Names are cut and cleaned of URL secrets as payload strings are.
        """
        if not settings.LOGS_BACKEND:
            return
        event_data = {
            'account_id': account_id,
            'object_id': object_id,
            'workflow_id': workflow_id,
            'task_id': task_id,
            'payload': payload,
            'object_name': object_name,
            'account_name': account_name,
        }
        for name, value in event_data.items():
            if callable(value):
                event_data[name] = value()
        for name in ('object_name', 'account_name'):
            if event_data[name] is not None:
                event_data[name] = without_url_secrets(
                    str(event_data[name]),
                )[:PAYLOAD_STR_MAX]
        context = request_context.get()
        if context is None:
            context = RequestContext()
        actor = None
        if user is None:
            auth_type = None
        else:
            actor = Actor(id=user.id, email=user.email, user_type=user.type)
        event = Event(
            type=event_type,
            category=event_category,
            service=settings.LOGS_SERVICE_NAME,
            ts=timezone.now(),
            account_id=event_data['account_id'],
            actor=actor,
            auth_type=auth_type,
            object=EventObject(
                type=event_category,
                id=event_data['object_id'],
                name=event_data['object_name'],
            ),
            payload=normalize_payload(payload=event_data['payload']),
            workflow_id=event_data['workflow_id'],
            task_id=event_data['task_id'],
            ip=context.ip,
            user_agent=context.user_agent,
            request_id=context.request_id,
            account_name=event_data['account_name'],
        )
        transaction.on_commit(lambda: cls._write(event=event))

    @classmethod
    def _write(cls, event: Event):
        """Keep a failed Redis write from breaking committed requests."""
        now = monotonic()
        if now < cls._circuit_open_until:
            cls._dropped += 1
            return
        try:
            get_stream().xadd(event=event)
        except Exception as exc:  # noqa: BLE001
            cls._circuit_open_until = now + CIRCUIT_OPEN_SECONDS
            error = type(exc).__name__
            logger.warning('Events stream is unavailable: %s', error)
            capture_sentry_message_throttled(
                message='Events stream is unavailable',
                data={'error': error, 'dropped': cls._dropped},
            )
            return
        if cls._dropped:
            logger.warning(
                'Events stream is back, events dropped meanwhile: %s',
                cls._dropped,
            )
            cls._dropped = 0

    @classmethod
    def user_logged_in(cls, user, source: str):
        """Record user logged in.

        user: accounts.User
        """
        cls._event(
            event_category=EventCategory.USERS,
            event_type=UserEvents.LOGIN,
            user=user,
            auth_type=AuthTokenType.USER,
            object_id=user.id,
            payload=lambda: {'source': source},
            account_id=user.account_id,
            object_name=user.email,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def user_signed_up(cls, user, source: str):
        """Record user signed up.

        user: accounts.User
        """
        cls._event(
            event_category=EventCategory.USERS,
            event_type=UserEvents.SIGNUP,
            user=user,
            auth_type=AuthTokenType.USER,
            object_id=user.id,
            payload=lambda: {'source': source},
            account_id=user.account_id,
            object_name=user.email,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def login_failed(
        cls,
        reason: LoginFailedReason.LITERALS,
        email: Optional[str],
    ):
        """Record login failed."""
        cls._event(
            event_category=EventCategory.USERS,
            event_type=UserEvents.LOGIN_FAILED,
            account_id=NO_ACCOUNT,
            payload=lambda: {
                'email': str(email or '').strip().lower(),
                'reason': reason,
            },
            user=None,
            auth_type=None,
            object_name=lambda: str(email or '').strip().lower(),
            account_name=None,
        )

    @classmethod
    def user_logged_out(cls, user, auth_type: Optional[str]):
        """Record user logged out.

        user: accounts.User
        """
        cls._event(
            event_category=EventCategory.USERS,
            event_type=UserEvents.LOGOUT,
            user=user,
            auth_type=auth_type,
            object_id=user.id,
            account_id=user.account_id,
            object_name=user.email,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def user_logged_out_by_provider(cls, target, source: str):
        """Record user logged out by provider.

        target: accounts.User or None
        """
        account_id = NO_ACCOUNT
        object_id = None
        object_name = None
        account_name = None
        if target is not None:
            account_id = target.account_id
            object_id = target.id
            object_name = target.email
            account_name = SimpleLazyObject(lambda: target.account.name)
        cls._event(
            event_category=EventCategory.USERS,
            event_type=UserEvents.LOGOUT,
            user=None,
            auth_type=None,
            payload=lambda: {
                'source': source,
                'reason': LogoutReason.IDENTITY_PROVIDER,
            },
            account_id=account_id,
            object_id=object_id,
            object_name=object_name,
            account_name=account_name,
        )

    @classmethod
    def superuser_logged_in_as(
        cls,
        user,
        auth_type: Optional[str],
        target,
    ):
        """Record superuser logged in as.

        user: accounts.User or None
        target: accounts.User
        """
        cls._event(
            event_category=EventCategory.USERS,
            event_type=UserEvents.LOGIN_AS,
            user=user,
            auth_type=auth_type,
            object_id=target.id,
            payload=lambda: {'target_email': target.email},
            account_id=target.account_id,
            object_name=target.email,
            account_name=lambda: target.account.name,
        )

    @classmethod
    def tenant_logged_in_as(
        cls,
        user,
        auth_type: Optional[str],
        tenant_account,
    ):
        """Record tenant logged in as.

        user: accounts.User
        tenant_account: accounts.Account
        """
        cls._event(
            event_category=EventCategory.ACCOUNTS,
            event_type=AccountEvents.TENANT_LOGIN_AS,
            user=user,
            auth_type=auth_type,
            object_id=tenant_account.id,
            payload=lambda: {
                'master_account_id': user.account_id,
                'master_account_name': user.account.name,
                'tenant_name': tenant_account.tenant_name,
            },
            account_id=tenant_account.id,
            object_name=tenant_account.tenant_name or tenant_account.name,
            account_name=tenant_account.name,
        )

    @classmethod
    def password_reset_requested(cls, target):
        """Record password reset requested.

        target: accounts.User
        """
        cls._event(
            event_category=EventCategory.USERS,
            event_type=UserEvents.PASSWORD_RESET_REQUEST,
            user=None,
            auth_type=None,
            object_id=target.id,
            payload=lambda: {'target_email': target.email},
            account_id=target.account_id,
            object_name=target.email,
            account_name=lambda: target.account.name,
        )

    @classmethod
    def password_reset(cls, user):
        """Record password reset.

        user: accounts.User
        """
        cls._event(
            event_category=EventCategory.USERS,
            event_type=UserEvents.PASSWORD_RESET,
            user=user,
            auth_type=None,
            object_id=user.id,
            payload=None,
            account_id=user.account_id,
            object_name=user.email,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def password_changed(cls, user, auth_type: Optional[str]):
        """Record password changed.

        user: accounts.User
        """
        cls._event(
            event_category=EventCategory.USERS,
            event_type=UserEvents.PASSWORD_CHANGE,
            user=user,
            auth_type=auth_type,
            object_id=user.id,
            account_id=user.account_id,
            object_name=user.email,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def password_set(cls, user, auth_type: Optional[str], target):
        """Record password set.

        user: accounts.User or None
        target: accounts.User
        """
        if user is not None and user.id == target.id:
            cls.password_changed(user=user, auth_type=auth_type)
            return
        cls._event(
            event_category=EventCategory.USERS,
            event_type=UserEvents.PASSWORD_SET,
            user=user,
            auth_type=auth_type,
            object_id=target.id,
            payload=lambda: {'target_email': target.email},
            account_id=target.account_id,
            object_name=target.email,
            account_name=lambda: target.account.name,
        )

    @classmethod
    def user_created(cls, user, auth_type: Optional[str], target):
        """Record user created.

        user: accounts.User
        target: accounts.User
        """
        cls._event(
            event_category=EventCategory.USERS,
            event_type=UserEvents.CREATE,
            user=user,
            auth_type=auth_type,
            object_id=target.id,
            payload=lambda: {
                'target_email': target.email,
                'is_admin': target.is_admin,
            },
            account_id=user.account_id,
            object_name=target.email,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def user_updated(
        cls,
        user,
        auth_type: Optional[str],
        target,
        update_kwargs: Dict[str, Any],
        user_groups: Optional[list] = None,
        subordinates: Optional[list] = None,
        is_password_set: bool = False,
    ):
        """Record user updated.

        user: accounts.User or None
        target: accounts.User
        user_groups: List[accounts.UserGroup or int] or None
        subordinates: List[accounts.User] or None
        """
        payload: Dict[str, Any] = {
            'target_email': target.email,
            **update_kwargs,
        }
        if user_groups is not None:
            group_ids = SimpleLazyObject(
                lambda: [getattr(group, 'pk', group) for group in user_groups],
            )
            payload['user_groups'] = group_ids
            payload['groups'] = SimpleLazyObject(
                lambda: {
                    group.id: group.name
                    for group in target.user_groups.filter(
                        id__in=list(group_ids),
                    )
                },
            )
        if subordinates is not None:
            payload['subordinates'] = SimpleLazyObject(
                lambda: [item.id for item in subordinates],
            )
            payload['subordinate_users'] = SimpleLazyObject(
                lambda: {
                    subordinate.id: subordinate.email
                    for subordinate in subordinates
                },
            )
        cls._event(
            event_category=EventCategory.USERS,
            event_type=UserEvents.UPDATE,
            user=user,
            auth_type=auth_type,
            object_id=target.id,
            payload=payload,
            account_id=target.account_id,
            object_name=target.email,
            account_name=lambda: target.account.name,
        )
        if 'is_admin' in update_kwargs:
            cls.user_admin_toggled(
                user=user,
                auth_type=auth_type,
                target=target,
            )
        if is_password_set:
            cls.password_set(user=user, auth_type=auth_type, target=target)

    @classmethod
    def user_admin_toggled(
        cls,
        user,
        auth_type: Optional[str],
        target,
    ):
        """Record user admin toggled.

        user: accounts.User or None
        target: accounts.User
        """
        cls._event(
            event_category=EventCategory.USERS,
            event_type=UserEvents.ADMIN_TOGGLE,
            user=user,
            auth_type=auth_type,
            object_id=target.id,
            payload=lambda: {
                'is_admin': target.is_admin,
                'target_email': target.email,
            },
            account_id=target.account_id,
            object_name=target.email,
            account_name=lambda: target.account.name,
        )

    @classmethod
    def user_deactivated(cls, user, auth_type: Optional[str], target):
        """Record user deactivated.

        user: accounts.User or None
        target: accounts.User
        """
        cls._event(
            event_category=EventCategory.USERS,
            event_type=UserEvents.DEACTIVATE,
            user=user,
            auth_type=auth_type,
            object_id=target.id,
            payload=lambda: {'target_email': target.email},
            account_id=target.account_id,
            object_name=target.email,
            account_name=lambda: target.account.name,
        )

    @classmethod
    def user_transferred(
        cls,
        user,
        auth_type: Optional[str],
        prev_user,
    ):
        """Record user transferred.

        user: accounts.User
        prev_user: accounts.User
        """
        cls._event(
            event_category=EventCategory.USERS,
            event_type=UserEvents.TRANSFER,
            user=user,
            auth_type=auth_type,
            object_id=user.id,
            payload=lambda: {
                'prev_account_id': prev_user.account_id,
                'prev_user_id': prev_user.id,
                'prev_account_name': prev_user.account.name,
                'prev_user_email': prev_user.email,
            },
            account_id=user.account_id,
            object_name=user.email,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def user_reassigned(
        cls,
        user,
        auth_type: Optional[str],
        old_user=None,
        new_user=None,
        old_group=None,
        new_group=None,
    ):
        """Record user reassigned.

        user: accounts.User
        old_user: accounts.User
        new_user: accounts.User
        old_group: accounts.UserGroup or None
        new_group: accounts.UserGroup or None
        """
        if old_user is not None:
            object_id = old_user.id
            object_name = old_user.email
        else:
            object_id = old_group.id
            object_name = old_group.name
        payload = {
            'old_user_id': getattr(old_user, 'id', None),
            'old_group_id': getattr(old_group, 'id', None),
            'new_user_id': getattr(new_user, 'id', None),
            'new_group_id': getattr(new_group, 'id', None),
            'old_user_email': getattr(old_user, 'email', None),
            'new_user_email': getattr(new_user, 'email', None),
            'old_group_name': getattr(old_group, 'name', None),
            'new_group_name': getattr(new_group, 'name', None),
        }
        cls._event(
            event_category=EventCategory.USERS,
            event_type=UserEvents.REASSIGN,
            user=user,
            auth_type=auth_type,
            object_id=object_id,
            payload=payload,
            account_id=user.account_id,
            object_name=object_name,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def user_unsubscribed(cls, user, email_type: str):
        """Record user unsubscribed.

        user: accounts.User
        """
        cls._event(
            event_category=EventCategory.USERS,
            event_type=UserEvents.UNSUBSCRIBE,
            user=user,
            auth_type=None,
            object_id=user.id,
            payload=lambda: {'email_type': email_type},
            account_id=user.account_id,
            object_name=user.email,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def vacation_activated(
        cls,
        user,
        auth_type: Optional[str],
        target,
        substitute_users,
        absence_status: str,
        start_date: Optional[date],
        end_date: Optional[date],
        delegated_tasks_count: int,
        is_update: bool,
    ):
        """Record vacation activated.

        user: accounts.User or None
        target: accounts.User
        substitute_users: Iterable[accounts.User]
        """
        substitutes = SimpleLazyObject(lambda: list(substitute_users))
        cls._event(
            event_category=EventCategory.USERS,
            event_type=UserEvents.VACATION_ACTIVATE,
            user=user,
            auth_type=auth_type,
            object_id=target.id,
            payload=lambda: {
                'target_email': target.email,
                'substitute_user_ids': sorted(
                    substitute.id for substitute in substitutes
                ),
                'absence_status': absence_status,
                'start_date': start_date,
                'end_date': end_date,
                'delegated_tasks_count': delegated_tasks_count,
                'is_update': is_update,
                'substitute_users': {
                    substitute.id: substitute.email
                    for substitute in substitutes
                },
            },
            account_id=target.account_id,
            object_name=target.email,
            account_name=lambda: target.account.name,
        )

    @classmethod
    def vacation_deactivated(
        cls,
        user,
        auth_type: Optional[str],
        target,
    ):
        """Record vacation deactivated.

        user: accounts.User or None
        target: accounts.User
        """
        cls._event(
            event_category=EventCategory.USERS,
            event_type=UserEvents.VACATION_DEACTIVATE,
            user=user,
            auth_type=auth_type,
            object_id=target.id,
            payload=lambda: {'target_email': target.email},
            account_id=target.account_id,
            object_name=target.email,
            account_name=lambda: target.account.name,
        )

    @classmethod
    def account_updated(
        cls,
        user,
        auth_type: Optional[str],
        account,
        update_kwargs: Dict[str, Any],
    ):
        """Record account updated.

        user: accounts.User
        account: accounts.Account
        """
        cls._event(
            event_category=EventCategory.ACCOUNTS,
            event_type=AccountEvents.UPDATE,
            user=user,
            auth_type=auth_type,
            object_id=account.id,
            payload=update_kwargs,
            account_id=user.account_id,
            object_name=account.name,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def account_verified(cls, user):
        """Record account verified.

        user: accounts.User
        """
        cls._event(
            event_category=EventCategory.ACCOUNTS,
            event_type=AccountEvents.VERIFY,
            user=user,
            auth_type=None,
            object_id=user.account_id,
            account_id=user.account_id,
            object_name=lambda: user.account.name,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def verification_resent(
        cls,
        user,
        auth_type: Optional[str],
        account_owner,
    ):
        """Record verification resent.

        user: accounts.User
        account_owner: accounts.User
        """
        cls._event(
            event_category=EventCategory.ACCOUNTS,
            event_type=AccountEvents.VERIFICATION_RESEND,
            user=user,
            auth_type=auth_type,
            object_id=account_owner.account_id,
            payload=lambda: {'target_email': account_owner.email},
            account_id=user.account_id,
            object_name=lambda: account_owner.account.name,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def tenant_created(cls, user, auth_type: Optional[str], tenant):
        """Record tenant created.

        user: accounts.User
        tenant: accounts.Account
        """
        cls._event(
            event_category=EventCategory.ACCOUNTS,
            event_type=AccountEvents.TENANT_CREATE,
            user=user,
            auth_type=auth_type,
            object_id=tenant.id,
            payload=lambda: {
                'name': tenant.tenant_name,
                'billing_plan': tenant.billing_plan,
            },
            account_id=user.account_id,
            object_name=tenant.tenant_name or tenant.name,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def tenant_deleted(cls, user, auth_type: Optional[str], tenant):
        """Record tenant deleted.

        user: accounts.User
        tenant: accounts.Account
        """
        cls._event(
            event_category=EventCategory.ACCOUNTS,
            event_type=AccountEvents.TENANT_DELETE,
            user=user,
            auth_type=auth_type,
            object_id=tenant.id,
            payload=lambda: {
                'name': tenant.tenant_name,
                'billing_plan': tenant.billing_plan,
            },
            account_id=user.account_id,
            object_name=tenant.tenant_name or tenant.name,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def invite_created(
        cls,
        user,
        auth_type: Optional[str],
        invited_user,
        is_transfer: bool,
    ):
        """Record invite created.

        user: accounts.User
        invited_user: accounts.User
        """
        cls._event(
            event_category=EventCategory.USERS,
            event_type=UserEvents.INVITE_CREATE,
            user=user,
            auth_type=auth_type,
            payload=lambda: {
                'target_email': invited_user.email,
                'invited_user_id': invited_user.id,
                'is_transfer': is_transfer,
            },
            account_id=user.account_id,
            object_name=invited_user.email,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def invite_resent(
        cls,
        user,
        auth_type: Optional[str],
        invited_user,
        is_transfer: bool,
    ):
        """Record invite resent.

        user: accounts.User
        invited_user: accounts.User
        """
        cls._event(
            event_category=EventCategory.USERS,
            event_type=UserEvents.INVITE_RESEND,
            user=user,
            auth_type=auth_type,
            payload=lambda: {
                'target_email': invited_user.email,
                'invited_user_id': invited_user.id,
                'is_transfer': is_transfer,
            },
            account_id=user.account_id,
            object_name=invited_user.email,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def invite_accepted(cls, invited_user, invited_by):
        """Record an accepted invite.

        invited_user: accounts.User
        invited_by: accounts.User or None
        """
        payload = {'invited_by_id': None, 'invited_by_email': None}
        if invited_by is not None:
            payload = {
                'invited_by_id': invited_by.id,
                'invited_by_email': invited_by.email,
            }
        cls._event(
            event_category=EventCategory.USERS,
            event_type=UserEvents.INVITE_ACCEPT,
            user=invited_user,
            auth_type=None,
            payload=payload,
            account_id=invited_user.account_id,
            object_name=invited_user.email,
            account_name=lambda: invited_user.account.name,
        )

    @classmethod
    def group_created(
        cls,
        user,
        auth_type: Optional[str],
        group,
        users_ids: Optional[List[int]],
    ):
        """Record group created.

        user: accounts.User or None
        group: accounts.UserGroup
        """
        cls._event(
            event_category=EventCategory.GROUPS,
            event_type=GroupEvents.CREATE,
            user=user,
            auth_type=auth_type,
            object_id=group.id,
            payload=lambda: {
                'name': group.name,
                'users_ids': users_ids,
                'users': {
                    member.id: member.email
                    for member in group.users.filter(id__in=users_ids or [])
                },
            },
            account_id=group.account_id,
            object_name=group.name,
            account_name=lambda: group.account.name,
        )

    @classmethod
    def group_updated(
        cls,
        user,
        auth_type: Optional[str],
        group,
        update_kwargs: Dict[str, Any],
        users_ids: Optional[List[int]] = None,
    ):
        """Record group updated.

        user: accounts.User or None
        group: accounts.UserGroup
        """
        payload = dict(update_kwargs)
        payload.setdefault('name', group.name)
        if users_ids is not None:
            payload['users_ids'] = users_ids
            payload['users'] = SimpleLazyObject(
                lambda: {
                    member.id: member.email
                    for member in group.users.filter(id__in=users_ids)
                },
            )
        cls._event(
            event_category=EventCategory.GROUPS,
            event_type=GroupEvents.UPDATE,
            user=user,
            auth_type=auth_type,
            object_id=group.id,
            payload=payload,
            account_id=group.account_id,
            object_name=group.name,
            account_name=lambda: group.account.name,
        )

    @classmethod
    def group_deleted(
        cls,
        user,
        auth_type: Optional[str],
        group,
        users_ids: List[int],
    ):
        """Record group deleted.

        user: accounts.User or None
        group: accounts.UserGroup
        """
        cls._event(
            event_category=EventCategory.GROUPS,
            event_type=GroupEvents.DELETE,
            user=user,
            auth_type=auth_type,
            object_id=group.id,
            payload=lambda: {
                'name': group.name,
                'users_ids': users_ids,
                'users': {
                    member.id: member.email
                    for member in group.users.filter(id__in=users_ids or [])
                },
            },
            account_id=group.account_id,
            object_name=group.name,
            account_name=lambda: group.account.name,
        )

    @classmethod
    def api_key_created(cls, user, auth_type: Optional[str], api_key):
        """Record api key created.

        user: accounts.User or None
        api_key: accounts.APIKey
        """
        cls._event(
            event_category=EventCategory.API_KEYS,
            event_type=ApiKeyEvents.CREATE,
            user=user,
            auth_type=auth_type,
            object_id=api_key.id,
            payload=lambda: {
                'name': api_key.name,
                'target_user_id': api_key.user_id,
                'target_email': api_key.user.email,
            },
            account_id=api_key.account_id,
            object_name=api_key.name,
            account_name=lambda: api_key.account.name,
        )

    @classmethod
    def api_key_revoked(cls, user, auth_type: Optional[str], api_key):
        """Record api key revoked.

        user: accounts.User or None
        api_key: accounts.APIKey
        """
        cls._event(
            event_category=EventCategory.API_KEYS,
            event_type=ApiKeyEvents.REVOKE,
            user=user,
            auth_type=auth_type,
            object_id=api_key.id,
            payload=lambda: {
                'name': api_key.name,
                'target_user_id': api_key.user_id,
                'target_email': api_key.user.email,
            },
            account_id=api_key.account_id,
            object_name=api_key.name,
            account_name=lambda: api_key.account.name,
        )

    @classmethod
    def admin_created(
        cls,
        user,
        target,
        model: str,
        form_data: Optional[Dict[str, Any]],
        object_id,
        account_id: int,
        account_name: Optional[Union[str, Callable[[], Optional[str]]]],
    ):
        """Record a row changed by the Django admin.

        user: accounts.User
        target: django.db.models.Model
        object_id: int, str or None; invite acceptance keys are excluded.
        """
        cls._event(
            event_category=EventCategory.ADMIN,
            event_type=AdminEvents.CREATE,
            user=user,
            auth_type=None,
            object_id=object_id,
            object_name=lambda: str(target),
            account_id=account_id,
            payload=lambda: {'model': model, **(form_data or {})},
            account_name=account_name,
        )

    @classmethod
    def admin_updated(
        cls,
        user,
        target,
        model: str,
        form_data: Optional[Dict[str, Any]],
        is_password_set: bool,
        object_id,
        account_id: int,
        account_name: Optional[Union[str, Callable[[], Optional[str]]]],
    ):
        """Record a row changed by the Django admin.

        user: accounts.User
        target: django.db.models.Model
        object_id: int, str or None; invite acceptance keys are excluded.
        """
        cls._event(
            event_category=EventCategory.ADMIN,
            event_type=AdminEvents.UPDATE,
            user=user,
            auth_type=None,
            object_id=object_id,
            object_name=lambda: str(target),
            account_id=account_id,
            payload=lambda: {'model': model, **(form_data or {})},
            account_name=account_name,
        )
        if is_password_set:
            cls.password_set(user=user, auth_type=None, target=target)

    @classmethod
    def admin_deleted(
        cls,
        user,
        target,
        model: str,
        object_id,
        account_id: int,
        account_name: Optional[Union[str, Callable[[], Optional[str]]]],
    ):
        """Record a row changed by the Django admin.

        user: accounts.User
        target: django.db.models.Model
        object_id: int, str or None; invite acceptance keys are excluded.
        """
        cls._event(
            event_category=EventCategory.ADMIN,
            event_type=AdminEvents.DELETE,
            user=user,
            auth_type=None,
            object_id=object_id,
            object_name=lambda: str(target),
            account_id=account_id,
            payload=lambda: {'model': model},
            account_name=account_name,
        )

    @classmethod
    def purchase_made(
        cls,
        user,
        auth_type: Optional[str],
        products: List[Dict[str, Any]],
        product_names: Dict[str, str],
    ):
        """Record purchase made.

        user: accounts.User
        """
        quantity_by_code: Dict[str, int] = {}
        for product in products:
            code = product['code']
            quantity_by_code[code] = (
                quantity_by_code.get(code, 0) + product['quantity']
            )
        cls._event(
            event_category=EventCategory.BILLING,
            event_type=BillingEvents.PURCHASE,
            user=user,
            auth_type=auth_type,
            object_id=user.account_id,
            payload=lambda: {
                'products': quantity_by_code,
                'product_names': product_names,
            },
            account_id=user.account_id,
            object_name=lambda: user.account.name,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def subscription_cancelled(cls, user, auth_type: Optional[str]):
        """Record subscription cancelled.

        user: accounts.User
        """
        cls._event(
            event_category=EventCategory.BILLING,
            event_type=BillingEvents.SUBSCRIPTION_CANCEL,
            user=user,
            auth_type=auth_type,
            object_id=user.account_id,
            account_id=user.account_id,
            object_name=lambda: user.account.name,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def payment_confirmed(
        cls,
        user,
        auth_type: Optional[str],
        subscription_data: Optional[Dict[str, Any]],
    ):
        """Record payment confirmed.

        user: accounts.User
        """
        payload = (
            {
                'billing_plan': subscription_data['billing_plan'],
                'max_users': subscription_data['max_users'],
            }
            if subscription_data
            else {}
        )
        cls._event(
            event_category=EventCategory.BILLING,
            event_type=BillingEvents.PAYMENT_CONFIRM,
            user=user,
            auth_type=auth_type,
            object_id=user.account_id,
            payload=payload,
            account_id=user.account_id,
            object_name=lambda: user.account.name,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def webhook_subscribed(
        cls,
        user,
        auth_type: Optional[str],
        url: str,
        event: str,
    ):
        """Record webhook subscribed.

        user: accounts.User
        """
        cls._event(
            event_category=EventCategory.WEBHOOKS,
            event_type=WebhookEvents.SUBSCRIBE,
            user=user,
            auth_type=auth_type,
            payload=lambda: {'url': url, 'event': event},
            account_id=user.account_id,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def webhook_unsubscribed(
        cls,
        user,
        auth_type: Optional[str],
        event: str,
    ):
        """Record webhook unsubscribed.

        user: accounts.User
        """
        cls._event(
            event_category=EventCategory.WEBHOOKS,
            event_type=WebhookEvents.UNSUBSCRIBE,
            user=user,
            auth_type=auth_type,
            payload=lambda: {'event': event},
            account_id=user.account_id,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def template_created(
        cls,
        user,
        auth_type: Optional[str],
        template,
        source: Optional[str] = None,
    ):
        """Record template created.

        user: accounts.User
        template: processes.Template
        """
        template_saved_data = SimpleLazyObject(
            lambda: template.get_draft() or {},
        )
        template_saved_extra: Dict[str, Any] = {
            'template': template_saved_data,
        }
        if source:
            template_saved_extra['source'] = source
        cls._event(
            event_category=EventCategory.TEMPLATES,
            event_type=TemplateEvents.CREATE,
            user=user,
            auth_type=auth_type,
            object_id=template.id,
            payload=lambda: {
                'name': template_saved_data.get('name', template.name),
                'version': template.version,
                'is_active': template.is_active,
                **template_saved_extra,
            },
            account_id=user.account_id,
            object_name=lambda: template_saved_data.get('name', template.name),
            account_name=lambda: user.account.name,
        )

    @classmethod
    def template_updated(
        cls,
        user,
        auth_type: Optional[str],
        template,
    ):
        """Record template updated.

        user: accounts.User
        template: processes.Template
        """
        template_saved_data = SimpleLazyObject(
            lambda: template.get_draft() or {},
        )
        template_saved_extra: Dict[str, Any] = {
            'template': template_saved_data,
        }
        cls._event(
            event_category=EventCategory.TEMPLATES,
            event_type=TemplateEvents.UPDATE,
            user=user,
            auth_type=auth_type,
            object_id=template.id,
            payload=lambda: {
                'name': template_saved_data.get('name', template.name),
                'version': template.version,
                'is_active': template.is_active,
                **template_saved_extra,
            },
            account_id=user.account_id,
            object_name=lambda: template_saved_data.get('name', template.name),
            account_name=lambda: user.account.name,
        )

    @classmethod
    def template_cloned(
        cls,
        user,
        auth_type: Optional[str],
        template,
        name: str,
    ):
        """Record template cloned.

        user: accounts.User
        template: processes.Template
        """
        cls._event(
            event_category=EventCategory.TEMPLATES,
            event_type=TemplateEvents.CLONE,
            user=user,
            auth_type=auth_type,
            object_id=template.id,
            payload=lambda: {
                'name': name,
                'version': template.version,
                'is_active': template.is_active,
            },
            account_id=user.account_id,
            object_name=name,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def template_deleted(
        cls,
        user,
        auth_type: Optional[str],
        template,
    ):
        """Record template deleted.

        user: accounts.User
        template: processes.Template
        """
        cls._event(
            event_category=EventCategory.TEMPLATES,
            event_type=TemplateEvents.DELETE,
            user=user,
            auth_type=auth_type,
            object_id=template.id,
            payload=lambda: {
                'name': template.name,
                'version': template.version,
                'is_active': template.is_active,
            },
            account_id=user.account_id,
            object_name=template.name,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def templates_export(
        cls,
        user,
        auth_type: Optional[str],
        filters: Dict[str, Any],
    ):
        """Record templates export.

        user: accounts.User
        """
        cls._event(
            event_category=EventCategory.TEMPLATES,
            event_type=TemplateEvents.EXPORT,
            user=user,
            auth_type=auth_type,
            payload=lambda: {'filters': filters},
            account_id=user.account_id,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def template_discarded_changes(
        cls,
        user,
        auth_type: Optional[str],
        template,
        template_deleted: bool,
    ):
        """Record template discarded changes.

        user: accounts.User
        template: processes.Template
        """
        cls._event(
            event_category=EventCategory.TEMPLATES,
            event_type=TemplateEvents.DRAFT_DISCARD,
            user=user,
            auth_type=auth_type,
            object_id=template.id,
            payload=lambda: {
                'name': template.name,
                'version': template.version,
                'is_active': template.is_active,
                'template_deleted': template_deleted,
            },
            account_id=user.account_id,
            object_name=template.name,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def template_generated_with_ai(
        cls,
        user,
        auth_type: Optional[str],
    ):
        """Record template generated with ai.

        user: accounts.User
        """
        cls._event(
            event_category=EventCategory.TEMPLATES,
            event_type=TemplateEvents.AI_GENERATE,
            user=user,
            auth_type=auth_type,
            account_id=user.account_id,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def template_filled_from_library(
        cls,
        user,
        auth_type: Optional[str],
        system_template,
    ):
        """Record template filled from library.

        user: accounts.User
        system_template: processes.SystemTemplate
        """
        cls._event(
            event_category=EventCategory.TEMPLATES,
            event_type=TemplateEvents.LIBRARY_FILL,
            user=user,
            auth_type=auth_type,
            object_id=system_template.id,
            payload=lambda: {'name': system_template.name},
            account_id=user.account_id,
            object_name=system_template.name,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def library_templates_imported(
        cls,
        user,
        auth_type: Optional[str],
        templates_count: int,
    ):
        """Record library templates imported.

        user: accounts.User
        """
        cls._event(
            event_category=EventCategory.TEMPLATES,
            event_type=TemplateEvents.LIBRARY_IMPORT,
            user=user,
            auth_type=auth_type,
            payload=lambda: {'templates_count': templates_count},
            account_id=user.account_id,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def template_preset_created(
        cls,
        user,
        auth_type: Optional[str],
        preset,
    ):
        """Record template preset created.

        user: accounts.User
        preset: processes.TemplatePreset
        """
        payload = SimpleLazyObject(
            lambda: {
                'name': preset.name,
                'template_id': preset.template_id,
                'type': preset.type,
                'is_default': preset.is_default,
                'template_name': getattr(preset.template, 'name', None),
            },
        )
        cls._event(
            event_category=EventCategory.TEMPLATES,
            event_type=TemplateEvents.PRESET_CREATE,
            user=user,
            auth_type=auth_type,
            object_id=preset.id,
            payload=payload,
            account_id=user.account_id,
            object_name=preset.name,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def template_preset_updated(
        cls,
        user,
        auth_type: Optional[str],
        preset,
        update_kwargs: Dict[str, Any],
        fields: Optional[List[Dict[str, Any]]] = None,
    ):
        """Record template preset updated.

        user: accounts.User
        preset: processes.TemplatePreset
        """
        extra = dict(update_kwargs)
        if fields is not None:
            extra['fields'] = fields
        payload = SimpleLazyObject(
            lambda: {
                'name': preset.name,
                'template_id': preset.template_id,
                'type': preset.type,
                'is_default': preset.is_default,
                **(extra or {}),
                'template_name': getattr(preset.template, 'name', None),
            },
        )
        cls._event(
            event_category=EventCategory.TEMPLATES,
            event_type=TemplateEvents.PRESET_UPDATE,
            user=user,
            auth_type=auth_type,
            object_id=preset.id,
            payload=payload,
            account_id=user.account_id,
            object_name=preset.name,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def template_preset_deleted(
        cls,
        user,
        auth_type: Optional[str],
        preset,
    ):
        """Record template preset deleted.

        user: accounts.User
        preset: processes.TemplatePreset
        """
        payload = SimpleLazyObject(
            lambda: {
                'name': preset.name,
                'template_id': preset.template_id,
                'type': preset.type,
                'is_default': preset.is_default,
                'template_name': getattr(preset.template, 'name', None),
            },
        )
        cls._event(
            event_category=EventCategory.TEMPLATES,
            event_type=TemplateEvents.PRESET_DELETE,
            user=user,
            auth_type=auth_type,
            object_id=preset.id,
            payload=payload,
            account_id=user.account_id,
            object_name=preset.name,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def template_preset_set_default(
        cls,
        user,
        auth_type: Optional[str],
        preset,
    ):
        """Record template preset set default.

        user: accounts.User
        preset: processes.TemplatePreset
        """
        payload = SimpleLazyObject(
            lambda: {
                'name': preset.name,
                'template_id': preset.template_id,
                'type': preset.type,
                'is_default': preset.is_default,
                'template_name': getattr(preset.template, 'name', None),
            },
        )
        cls._event(
            event_category=EventCategory.TEMPLATES,
            event_type=TemplateEvents.PRESET_SET_DEFAULT,
            user=user,
            auth_type=auth_type,
            object_id=preset.id,
            payload=payload,
            account_id=user.account_id,
            object_name=preset.name,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def fieldset_created(
        cls,
        user,
        auth_type: Optional[str],
        fieldset,
    ):
        """Record fieldset created.

        user: accounts.User
        fieldset: processes.FieldsetTemplate
        """
        cls._event(
            event_category=EventCategory.TEMPLATES,
            event_type=TemplateEvents.FIELDSET_CREATE,
            user=user,
            auth_type=auth_type,
            object_id=fieldset.id,
            payload=lambda: {'name': fieldset.name},
            account_id=user.account_id,
            object_name=fieldset.name,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def fieldset_updated(
        cls,
        user,
        auth_type: Optional[str],
        fieldset,
        update_kwargs: Dict[str, Any],
        fields: Optional[List[Dict[str, Any]]] = None,
        rules: Optional[List[Dict[str, Any]]] = None,
    ):
        """Record fieldset updated.

        user: accounts.User
        fieldset: processes.FieldsetTemplate
        """
        extra = dict(update_kwargs)
        if fields is not None:
            extra['fields'] = fields
        if rules is not None:
            extra['rules'] = rules
        cls._event(
            event_category=EventCategory.TEMPLATES,
            event_type=TemplateEvents.FIELDSET_UPDATE,
            user=user,
            auth_type=auth_type,
            object_id=fieldset.id,
            payload=lambda: {'name': fieldset.name, **extra},
            account_id=user.account_id,
            object_name=fieldset.name,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def fieldset_cloned(
        cls,
        user,
        auth_type: Optional[str],
        clone,
        source_fieldset,
    ):
        """Record a cloned shared fieldset.

        user: accounts.User
        clone: processes.FieldsetTemplate
        source_fieldset: processes.FieldsetTemplate
        """
        cls._event(
            event_category=EventCategory.TEMPLATES,
            event_type=TemplateEvents.FIELDSET_CLONE,
            user=user,
            auth_type=auth_type,
            object_id=clone.id,
            payload=lambda: {
                'name': clone.name,
                'source_fieldset_id': source_fieldset.id,
                'source_fieldset_name': source_fieldset.name,
            },
            account_id=user.account_id,
            object_name=clone.name,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def fieldset_deleted(
        cls,
        user,
        auth_type: Optional[str],
        fieldset,
    ):
        """Record fieldset deleted.

        user: accounts.User
        fieldset: processes.FieldsetTemplate
        """
        cls._event(
            event_category=EventCategory.TEMPLATES,
            event_type=TemplateEvents.FIELDSET_DELETE,
            user=user,
            auth_type=auth_type,
            object_id=fieldset.id,
            payload=lambda: {'name': fieldset.name},
            account_id=user.account_id,
            object_name=fieldset.name,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def dataset_created(
        cls,
        user,
        auth_type: Optional[str],
        dataset,
        items_count: int,
    ):
        """Record dataset created.

        user: accounts.User
        dataset: datasets.Dataset
        """
        cls._event(
            event_category=EventCategory.DATASETS,
            event_type=DatasetEvents.CREATE,
            user=user,
            auth_type=auth_type,
            object_id=dataset.id,
            payload=lambda: {'name': dataset.name, 'items_count': items_count},
            account_id=user.account_id,
            object_name=dataset.name,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def dataset_updated(
        cls,
        user,
        auth_type: Optional[str],
        dataset,
        update_kwargs: Dict[str, Any],
    ):
        """Record dataset updated.

        user: accounts.User
        dataset: datasets.Dataset
        """
        cls._event(
            event_category=EventCategory.DATASETS,
            event_type=DatasetEvents.UPDATE,
            user=user,
            auth_type=auth_type,
            object_id=dataset.id,
            payload=lambda: {'name': dataset.name, **(update_kwargs or {})},
            account_id=user.account_id,
            object_name=dataset.name,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def dataset_deleted(cls, user, auth_type: Optional[str], dataset):
        """Record dataset deleted.

        user: accounts.User
        dataset: datasets.Dataset
        """
        cls._event(
            event_category=EventCategory.DATASETS,
            event_type=DatasetEvents.DELETE,
            user=user,
            auth_type=auth_type,
            object_id=dataset.id,
            payload=lambda: {'name': dataset.name},
            account_id=user.account_id,
            object_name=dataset.name,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def dataset_item_created(
        cls,
        user,
        auth_type: Optional[str],
        item,
    ):
        """Record dataset item created.

        user: accounts.User
        item: datasets.DatasetItem
        """
        cls._event(
            event_category=EventCategory.DATASETS,
            event_type=DatasetEvents.ITEM_CREATE,
            user=user,
            auth_type=auth_type,
            object_id=item.id,
            payload=lambda: {
                'dataset_id': item.dataset_id,
                'dataset_name': item.dataset.name,
                'value': item.value,
            },
            account_id=user.account_id,
            object_name=item.value,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def dataset_item_updated(
        cls,
        user,
        auth_type: Optional[str],
        item,
        update_kwargs: Dict[str, Any],
    ):
        """Record dataset item updated.

        user: accounts.User
        item: datasets.DatasetItem
        """
        cls._event(
            event_category=EventCategory.DATASETS,
            event_type=DatasetEvents.ITEM_UPDATE,
            user=user,
            auth_type=auth_type,
            object_id=item.id,
            payload=lambda: {
                'dataset_id': item.dataset_id,
                **(update_kwargs or {}),
                'dataset_name': item.dataset.name,
                'value': item.value,
            },
            account_id=user.account_id,
            object_name=item.value,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def dataset_item_deleted(
        cls,
        user,
        auth_type: Optional[str],
        item,
    ):
        """Record dataset item deleted.

        user: accounts.User
        item: datasets.DatasetItem
        """
        cls._event(
            event_category=EventCategory.DATASETS,
            event_type=DatasetEvents.ITEM_DELETE,
            user=user,
            auth_type=auth_type,
            object_id=item.id,
            payload=lambda: {
                'dataset_id': item.dataset_id,
                'dataset_name': item.dataset.name,
                'value': item.value,
            },
            account_id=user.account_id,
            object_name=item.value,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def workflow_run(cls, user, auth_type: Optional[str], workflow):
        """Record workflow run.

        user: accounts.User or None
        workflow: processes.Workflow
        """
        workflow_data: Dict[str, Any] = SimpleLazyObject(
            lambda: {
                'workflow_name': workflow.name,
                'template_id': workflow.template_id,
                'template_name': getattr(workflow.template, 'name', None),
            },
        )
        cls._event(
            event_category=EventCategory.WORKFLOWS,
            event_type=WorkflowEvents.RUN,
            user=user,
            auth_type=auth_type,
            object_id=workflow.id,
            payload=workflow_data,
            workflow_id=workflow.id,
            task_id=None,
            account_id=workflow.account_id,
            object_name=workflow.name,
            account_name=lambda: workflow.account.name,
        )

    @classmethod
    def sub_workflow_run(
        cls,
        user,
        auth_type: Optional[str],
        sub_workflow,
    ):
        """Record sub workflow run.

        user: accounts.User or None
        sub_workflow: processes.Workflow
        """
        ancestor_task = SimpleLazyObject(lambda: sub_workflow.ancestor_task)
        workflow_data: Dict[str, Any] = SimpleLazyObject(
            lambda: {
                'workflow_name': ancestor_task.workflow.name,
                'template_id': ancestor_task.workflow.template_id,
                'template_name': getattr(
                    ancestor_task.workflow.template,
                    'name',
                    None,
                ),
                'task_name': ancestor_task.name,
            },
        )
        cls._event(
            event_category=EventCategory.WORKFLOWS,
            event_type=WorkflowEvents.SUB_WORKFLOW_RUN,
            user=user,
            auth_type=auth_type,
            object_id=lambda: ancestor_task.workflow.id,
            payload=lambda: {
                **workflow_data,
                'sub_workflow_id': sub_workflow.id,
                'sub_workflow_name': sub_workflow.name,
            },
            workflow_id=lambda: ancestor_task.workflow.id,
            task_id=lambda: ancestor_task.id,
            account_id=lambda: ancestor_task.workflow.account_id,
            object_name=lambda: ancestor_task.workflow.name,
            account_name=lambda: ancestor_task.workflow.account.name,
        )

    @classmethod
    def workflow_updated(
        cls,
        user,
        auth_type: Optional[str],
        workflow,
        update_kwargs: Dict[str, Any],
    ):
        """Record workflow updated.

        user: accounts.User or None
        workflow: processes.Workflow
        """
        workflow_data: Dict[str, Any] = SimpleLazyObject(
            lambda: {
                'workflow_name': workflow.name,
                'template_id': workflow.template_id,
                'template_name': getattr(workflow.template, 'name', None),
            },
        )
        payload = dict(update_kwargs)
        kickoff = update_kwargs.get('kickoff')
        if kickoff:
            payload['kickoff_fields'] = SimpleLazyObject(
                lambda: dict(
                    workflow.fields.filter(
                        kickoff__isnull=False,
                        api_name__in=list(kickoff),
                    ).values_list('api_name', 'name'),
                ),
            )
        cls._event(
            event_category=EventCategory.WORKFLOWS,
            event_type=WorkflowEvents.UPDATE,
            user=user,
            auth_type=auth_type,
            object_id=workflow.id,
            payload=lambda: {**workflow_data, **payload},
            workflow_id=workflow.id,
            task_id=None,
            account_id=workflow.account_id,
            object_name=workflow.name,
            account_name=lambda: workflow.account.name,
        )

    @classmethod
    def workflow_snooze(
        cls,
        user,
        auth_type: Optional[str],
        workflow,
        snooze_until: datetime,
    ):
        """Record workflow snooze.

        user: accounts.User or None
        workflow: processes.Workflow
        """
        workflow_data: Dict[str, Any] = SimpleLazyObject(
            lambda: {
                'workflow_name': workflow.name,
                'template_id': workflow.template_id,
                'template_name': getattr(workflow.template, 'name', None),
            },
        )
        cls._event(
            event_category=EventCategory.WORKFLOWS,
            event_type=WorkflowEvents.FORCE_DELAY,
            user=user,
            auth_type=auth_type,
            object_id=workflow.id,
            payload=lambda: {**workflow_data, 'date': snooze_until},
            workflow_id=workflow.id,
            task_id=None,
            account_id=workflow.account_id,
            object_name=workflow.name,
            account_name=lambda: workflow.account.name,
        )

    @classmethod
    def workflow_resume(cls, user, auth_type: Optional[str], workflow):
        """Record workflow resume.

        user: accounts.User or None
        workflow: processes.Workflow
        """
        workflow_data: Dict[str, Any] = SimpleLazyObject(
            lambda: {
                'workflow_name': workflow.name,
                'template_id': workflow.template_id,
                'template_name': getattr(workflow.template, 'name', None),
            },
        )
        cls._event(
            event_category=EventCategory.WORKFLOWS,
            event_type=WorkflowEvents.FORCE_RESUME,
            user=user,
            auth_type=auth_type,
            object_id=workflow.id,
            payload=workflow_data,
            workflow_id=workflow.id,
            task_id=None,
            account_id=workflow.account_id,
            object_name=workflow.name,
            account_name=lambda: workflow.account.name,
        )

    @classmethod
    def workflow_finish(cls, user, auth_type: Optional[str], workflow):
        """Record workflow finish.

        user: accounts.User or None
        workflow: processes.Workflow
        """
        workflow_data: Dict[str, Any] = SimpleLazyObject(
            lambda: {
                'workflow_name': workflow.name,
                'template_id': workflow.template_id,
                'template_name': getattr(workflow.template, 'name', None),
            },
        )
        cls._event(
            event_category=EventCategory.WORKFLOWS,
            event_type=WorkflowEvents.ENDED,
            user=user,
            auth_type=auth_type,
            object_id=workflow.id,
            payload=workflow_data,
            workflow_id=workflow.id,
            task_id=None,
            account_id=workflow.account_id,
            object_name=workflow.name,
            account_name=lambda: workflow.account.name,
        )

    @classmethod
    def workflow_complete(
        cls,
        user,
        auth_type: Optional[str],
        workflow,
        task,
    ):
        """Record workflow complete.

        user: accounts.User or None
        workflow: processes.Workflow
        task: processes.Task or None
        """
        workflow_data: Dict[str, Any] = SimpleLazyObject(
            lambda: {
                'workflow_name': workflow.name,
                'template_id': workflow.template_id,
                'template_name': getattr(workflow.template, 'name', None),
                'task_name': getattr(task, 'name', None),
            },
        )
        cls._event(
            event_category=EventCategory.WORKFLOWS,
            event_type=WorkflowEvents.COMPLETE,
            user=user,
            auth_type=auth_type,
            object_id=workflow.id,
            payload=workflow_data,
            workflow_id=workflow.id,
            task_id=getattr(task, 'id', None),
            account_id=workflow.account_id,
            object_name=workflow.name,
            account_name=lambda: workflow.account.name,
        )

    @classmethod
    def workflow_ended_by_condition(
        cls,
        user,
        auth_type: Optional[str],
        workflow,
        task,
    ):
        """Record workflow ended by condition.

        user: accounts.User or None
        workflow: processes.Workflow
        task: processes.Task or None
        """
        workflow_data: Dict[str, Any] = SimpleLazyObject(
            lambda: {
                'workflow_name': workflow.name,
                'template_id': workflow.template_id,
                'template_name': getattr(workflow.template, 'name', None),
                'task_name': getattr(task, 'name', None),
            },
        )
        cls._event(
            event_category=EventCategory.WORKFLOWS,
            event_type=WorkflowEvents.ENDED_BY_CONDITION,
            user=user,
            auth_type=auth_type,
            object_id=workflow.id,
            payload=workflow_data,
            workflow_id=workflow.id,
            task_id=getattr(task, 'id', None),
            account_id=workflow.account_id,
            object_name=workflow.name,
            account_name=lambda: workflow.account.name,
        )

    @classmethod
    def workflow_return(cls, user, auth_type: Optional[str], task):
        """Record workflow return.

        user: accounts.User or None
        task: processes.Task
        """
        workflow_data: Dict[str, Any] = SimpleLazyObject(
            lambda: {
                'workflow_name': task.workflow.name,
                'template_id': task.workflow.template_id,
                'template_name': getattr(task.workflow.template, 'name', None),
                'task_name': task.name,
            },
        )
        cls._event(
            event_category=EventCategory.WORKFLOWS,
            event_type=WorkflowEvents.REVERT,
            user=user,
            auth_type=auth_type,
            object_id=lambda: task.workflow.id,
            payload=workflow_data,
            workflow_id=lambda: task.workflow.id,
            task_id=task.id,
            account_id=lambda: task.workflow.account_id,
            object_name=lambda: task.workflow.name,
            account_name=lambda: task.workflow.account.name,
        )

    @classmethod
    def workflow_urgent(cls, user, auth_type: Optional[str], workflow):
        """Record workflow urgent.

        user: accounts.User or None
        workflow: processes.Workflow
        """
        workflow_data: Dict[str, Any] = SimpleLazyObject(
            lambda: {
                'workflow_name': workflow.name,
                'template_id': workflow.template_id,
                'template_name': getattr(workflow.template, 'name', None),
            },
        )
        event_type = (
            WorkflowEvents.URGENT
            if workflow.is_urgent
            else WorkflowEvents.NOT_URGENT
        )
        cls._event(
            event_category=EventCategory.WORKFLOWS,
            event_type=event_type,
            user=user,
            auth_type=auth_type,
            object_id=workflow.id,
            payload=workflow_data,
            workflow_id=workflow.id,
            task_id=None,
            account_id=workflow.account_id,
            object_name=workflow.name,
            account_name=lambda: workflow.account.name,
        )

    @classmethod
    def workflow_terminated(
        cls,
        user,
        auth_type: Optional[str],
        workflow,
    ):
        """Record workflow terminated.

        user: accounts.User or None
        workflow: processes.Workflow
        """
        workflow_data: Dict[str, Any] = SimpleLazyObject(
            lambda: {
                'workflow_name': workflow.name,
                'template_id': workflow.template_id,
                'template_name': getattr(workflow.template, 'name', None),
            },
        )
        cls._event(
            event_category=EventCategory.WORKFLOWS,
            event_type=WorkflowEvents.TERMINATE,
            user=user,
            auth_type=auth_type,
            object_id=workflow.id,
            payload=workflow_data,
            workflow_id=workflow.id,
            task_id=None,
            account_id=workflow.account_id,
            object_name=workflow.name,
            account_name=lambda: workflow.account.name,
        )

    @classmethod
    def task_start(cls, task):
        """Record task start.

        task: processes.Task
        """
        cls._event(
            event_category=EventCategory.TASKS,
            event_type=TaskEvents.START,
            user=None,
            auth_type=None,
            object_id=task.id,
            payload=lambda: {
                'workflow_name': task.workflow.name,
                'task_number': task.number,
                'task_name': task.name,
            },
            workflow_id=task.workflow_id,
            task_id=task.id,
            account_id=task.account_id,
            object_name=task.name,
            account_name=lambda: task.account.name,
        )

    @classmethod
    def task_complete(cls, user, auth_type: Optional[str], task):
        """Record task complete.

        user: accounts.User or None
        task: processes.Task
        """
        cls._event(
            event_category=EventCategory.TASKS,
            event_type=TaskEvents.COMPLETE,
            user=user,
            auth_type=auth_type,
            object_id=task.id,
            payload=lambda: {
                'workflow_name': task.workflow.name,
                'task_number': task.number,
                'task_name': task.name,
            },
            workflow_id=task.workflow_id,
            task_id=task.id,
            account_id=task.account_id,
            object_name=task.name,
            account_name=lambda: task.account.name,
        )

    @classmethod
    def task_revert(cls, user, auth_type: Optional[str], task):
        """Record task revert.

        user: accounts.User or None
        task: processes.Task
        """
        cls._event(
            event_category=EventCategory.TASKS,
            event_type=TaskEvents.REVERT,
            user=user,
            auth_type=auth_type,
            object_id=task.id,
            payload=lambda: {
                'workflow_name': task.workflow.name,
                'task_number': task.number,
                'task_name': task.name,
            },
            workflow_id=task.workflow_id,
            task_id=task.id,
            account_id=task.account_id,
            object_name=task.name,
            account_name=lambda: task.account.name,
        )

    @classmethod
    def task_skip(cls, task):
        """Record task skip.

        task: processes.Task
        """
        cls._event(
            event_category=EventCategory.TASKS,
            event_type=TaskEvents.SKIP,
            user=None,
            auth_type=None,
            object_id=task.id,
            payload=lambda: {
                'workflow_name': task.workflow.name,
                'task_number': task.number,
                'task_name': task.name,
            },
            workflow_id=task.workflow_id,
            task_id=task.id,
            account_id=task.account_id,
            object_name=task.name,
            account_name=lambda: task.account.name,
        )

    @classmethod
    def task_skip_no_performers(cls, task):
        """Record task skip no performers.

        task: processes.Task
        """
        cls._event(
            event_category=EventCategory.TASKS,
            event_type=TaskEvents.SKIP_NO_PERFORMERS,
            user=None,
            auth_type=None,
            object_id=task.id,
            payload=lambda: {
                'workflow_name': task.workflow.name,
                'task_number': task.number,
                'task_name': task.name,
            },
            workflow_id=task.workflow_id,
            task_id=task.id,
            account_id=task.account_id,
            object_name=task.name,
            account_name=lambda: task.account.name,
        )

    @classmethod
    def task_delay(cls, task):
        """Record task delay.

        task: processes.Task
        """
        cls._event(
            event_category=EventCategory.TASKS,
            event_type=TaskEvents.DELAY,
            user=None,
            auth_type=None,
            object_id=task.id,
            payload=lambda: {
                'workflow_name': task.workflow.name,
                'task_number': task.number,
                'task_name': task.name,
            },
            workflow_id=task.workflow_id,
            task_id=task.id,
            account_id=task.account_id,
            object_name=task.name,
            account_name=lambda: task.account.name,
        )

    @classmethod
    def task_due_date_changed(
        cls,
        user,
        auth_type: Optional[str],
        task,
    ):
        """Record task due date changed.

        user: accounts.User or None
        task: processes.Task
        """
        cls._event(
            event_category=EventCategory.TASKS,
            event_type=TaskEvents.DUE_DATE_CHANGED,
            user=user,
            auth_type=auth_type,
            object_id=task.id,
            payload=lambda: {
                'workflow_name': task.workflow.name,
                'task_number': task.number,
                'task_name': task.name,
                'due_date': task.due_date,
            },
            workflow_id=task.workflow_id,
            task_id=task.id,
            account_id=task.account_id,
            object_name=task.name,
            account_name=lambda: task.account.name,
        )

    @classmethod
    def task_performer_created(
        cls,
        user,
        auth_type: Optional[str],
        task,
        performer,
    ):
        """Record task performer created.

        user: accounts.User or None
        task: processes.Task
        performer: accounts.User
        """
        cls._event(
            event_category=EventCategory.TASKS,
            event_type=TaskEvents.PERFORMER_CREATED,
            user=user,
            auth_type=auth_type,
            object_id=task.id,
            payload=lambda: {
                'workflow_name': task.workflow.name,
                'task_number': task.number,
                'task_name': task.name,
                'target_user_id': performer.id,
                'target_email': performer.email,
            },
            workflow_id=task.workflow_id,
            task_id=task.id,
            account_id=task.account_id,
            object_name=task.name,
            account_name=lambda: task.account.name,
        )

    @classmethod
    def task_performer_deleted(
        cls,
        user,
        auth_type: Optional[str],
        task,
        performer,
    ):
        """Record task performer deleted.

        user: accounts.User or None
        task: processes.Task
        performer: accounts.User
        """
        cls._event(
            event_category=EventCategory.TASKS,
            event_type=TaskEvents.PERFORMER_DELETED,
            user=user,
            auth_type=auth_type,
            object_id=task.id,
            payload=lambda: {
                'workflow_name': task.workflow.name,
                'task_number': task.number,
                'task_name': task.name,
                'target_user_id': performer.id,
                'target_email': performer.email,
            },
            workflow_id=task.workflow_id,
            task_id=task.id,
            account_id=task.account_id,
            object_name=task.name,
            account_name=lambda: task.account.name,
        )

    @classmethod
    def task_performer_group_created(
        cls,
        user,
        auth_type: Optional[str],
        task,
        group,
    ):
        """Record task performer group created.

        user: accounts.User or None
        task: processes.Task
        group: accounts.UserGroup
        """
        cls._event(
            event_category=EventCategory.TASKS,
            event_type=TaskEvents.PERFORMER_GROUP_CREATED,
            user=user,
            auth_type=auth_type,
            object_id=task.id,
            payload=lambda: {
                'workflow_name': task.workflow.name,
                'task_number': task.number,
                'task_name': task.name,
                'target_group_id': group.id,
                'group_name': group.name,
            },
            workflow_id=task.workflow_id,
            task_id=task.id,
            account_id=task.account_id,
            object_name=task.name,
            account_name=lambda: task.account.name,
        )

    @classmethod
    def task_performer_group_deleted(
        cls,
        user,
        auth_type: Optional[str],
        task,
        group,
    ):
        """Record task performer group deleted.

        user: accounts.User or None
        task: processes.Task
        group: accounts.UserGroup
        """
        cls._event(
            event_category=EventCategory.TASKS,
            event_type=TaskEvents.PERFORMER_GROUP_DELETED,
            user=user,
            auth_type=auth_type,
            object_id=task.id,
            payload=lambda: {
                'workflow_name': task.workflow.name,
                'task_number': task.number,
                'task_name': task.name,
                'target_group_id': group.id,
                'group_name': group.name,
            },
            workflow_id=task.workflow_id,
            task_id=task.id,
            account_id=task.account_id,
            object_name=task.name,
            account_name=lambda: task.account.name,
        )

    @classmethod
    def task_delegation(cls, task, target, substitute_group):
        """Record task delegation.

        task: processes.Task
        target: accounts.User
        substitute_group: accounts.UserGroup
        """
        cls._event(
            event_category=EventCategory.TASKS,
            event_type=TaskEvents.DELEGATION,
            user=None,
            auth_type=None,
            object_id=task.id,
            payload=lambda: {
                'workflow_name': task.workflow.name,
                'task_number': task.number,
                'task_name': task.name,
                'vacation_user_id': target.id,
                'substitute_group_id': substitute_group.id,
                'vacation_user_email': target.email,
                'substitute_group_name': substitute_group.name,
            },
            workflow_id=task.workflow_id,
            task_id=task.id,
            account_id=task.account_id,
            object_name=task.name,
            account_name=lambda: task.account.name,
        )

    @classmethod
    def comment_created(cls, user, auth_type: Optional[str], comment):
        """Record comment created.

        user: accounts.User
        comment: processes.WorkflowEvent
        """
        comment_data = SimpleLazyObject(
            lambda: {
                'workflow_name': comment.workflow.name,
                'task_name': getattr(comment.task, 'name', None),
            },
        )

        cls._event(
            event_category=EventCategory.TASKS,
            event_type=TaskEvents.COMMENT,
            user=user,
            auth_type=auth_type,
            object_id=comment.id,
            payload=lambda: {**comment_data},
            workflow_id=comment.workflow_id,
            task_id=comment.task_id,
            account_id=user.account_id,
            object_name=comment.text,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def comment_updated(cls, user, auth_type: Optional[str], comment):
        """Record comment updated.

        user: accounts.User
        comment: processes.WorkflowEvent
        """
        comment_data = SimpleLazyObject(
            lambda: {
                'workflow_name': comment.workflow.name,
                'task_name': getattr(comment.task, 'name', None),
            },
        )

        cls._event(
            event_category=EventCategory.TASKS,
            event_type=TaskEvents.COMMENT_UPDATE,
            user=user,
            auth_type=auth_type,
            object_id=comment.id,
            payload=lambda: {**comment_data},
            workflow_id=comment.workflow_id,
            task_id=comment.task_id,
            account_id=user.account_id,
            object_name=comment.text,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def comment_deleted(cls, user, auth_type: Optional[str], comment):
        """Record comment deleted.

        user: accounts.User
        comment: processes.WorkflowEvent
        """
        comment_data = SimpleLazyObject(
            lambda: {
                'workflow_name': comment.workflow.name,
                'task_name': getattr(comment.task, 'name', None),
            },
        )

        cls._event(
            event_category=EventCategory.TASKS,
            event_type=TaskEvents.COMMENT_DELETE,
            user=user,
            auth_type=auth_type,
            object_id=comment.id,
            payload=lambda: {**comment_data},
            workflow_id=comment.workflow_id,
            task_id=comment.task_id,
            account_id=user.account_id,
            object_name=comment.text,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def create_reaction(
        cls,
        user,
        auth_type: Optional[str],
        comment,
        value: str,
    ):
        """Record create reaction.

        user: accounts.User
        comment: processes.WorkflowEvent
        """
        comment_data = SimpleLazyObject(
            lambda: {
                'workflow_name': comment.workflow.name,
                'task_name': getattr(comment.task, 'name', None),
            },
        )

        cls._event(
            event_category=EventCategory.TASKS,
            event_type=TaskEvents.REACTION_CREATE,
            user=user,
            auth_type=auth_type,
            object_id=comment.id,
            payload=lambda: {**comment_data, 'reaction': value},
            workflow_id=comment.workflow_id,
            task_id=comment.task_id,
            account_id=user.account_id,
            object_name=comment.text,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def delete_reaction(
        cls,
        user,
        auth_type: Optional[str],
        comment,
        value: str,
    ):
        """Record delete reaction.

        user: accounts.User
        comment: processes.WorkflowEvent
        """
        comment_data = SimpleLazyObject(
            lambda: {
                'workflow_name': comment.workflow.name,
                'task_name': getattr(comment.task, 'name', None),
            },
        )

        cls._event(
            event_category=EventCategory.TASKS,
            event_type=TaskEvents.REACTION_DELETE,
            user=user,
            auth_type=auth_type,
            object_id=comment.id,
            payload=lambda: {**comment_data, 'reaction': value},
            workflow_id=comment.workflow_id,
            task_id=comment.task_id,
            account_id=user.account_id,
            object_name=comment.text,
            account_name=lambda: user.account.name,
        )

    @classmethod
    def checklist_item_marked(
        cls,
        user,
        auth_type: Optional[str],
        selection,
    ):
        """Record a checklist selection change.

        user: accounts.User
        selection: processes.ChecklistSelection
        """
        checklist = SimpleLazyObject(lambda: selection.checklist)
        task = SimpleLazyObject(lambda: checklist.task)
        cls._event(
            event_category=EventCategory.TASKS,
            event_type=TaskEvents.CHECKLIST_MARK,
            user=user,
            auth_type=auth_type,
            object_id=lambda: checklist.id,
            object_name=selection.value,
            account_id=lambda: task.account_id,
            workflow_id=lambda: task.workflow_id,
            task_id=lambda: task.id,
            payload=lambda: {
                'workflow_id': task.workflow_id,
                'workflow_name': task.workflow.name,
                'task_id': task.id,
                'task_name': task.name,
                'checklist_id': checklist.id,
                'checklist_api_name': checklist.api_name,
                'selection_id': selection.id,
                'selection_api_name': selection.api_name,
                'selection_value': selection.value,
            },
            account_name=lambda: task.account.name,
        )

    @classmethod
    def checklist_item_unmarked(
        cls,
        user,
        auth_type: Optional[str],
        selection,
    ):
        """Record a checklist selection change.

        user: accounts.User
        selection: processes.ChecklistSelection
        """
        checklist = SimpleLazyObject(lambda: selection.checklist)
        task = SimpleLazyObject(lambda: checklist.task)
        cls._event(
            event_category=EventCategory.TASKS,
            event_type=TaskEvents.CHECKLIST_UNMARK,
            user=user,
            auth_type=auth_type,
            object_id=lambda: checklist.id,
            object_name=selection.value,
            account_id=lambda: task.account_id,
            workflow_id=lambda: task.workflow_id,
            task_id=lambda: task.id,
            payload=lambda: {
                'workflow_id': task.workflow_id,
                'workflow_name': task.workflow.name,
                'task_id': task.id,
                'task_name': task.name,
                'checklist_id': checklist.id,
                'checklist_api_name': checklist.api_name,
                'selection_id': selection.id,
                'selection_api_name': selection.api_name,
                'selection_value': selection.value,
            },
            account_name=lambda: task.account.name,
        )
