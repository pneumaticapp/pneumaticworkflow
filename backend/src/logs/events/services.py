from datetime import date
from typing import Any, Dict, List, Optional, Union

from src.authentication.enums import AuthTokenType
from src.logs.events.emitter import NO_ACCOUNT, emit, logs_enabled
from src.logs.events.enums import (
    AccountEvents,
    AdminEvents,
    ApiKeyEvents,
    BillingEvents,
    DatasetEvents,
    EventObjectType,
    GroupEvents,
    LoginFailedReason,
    LogoutReason,
    TaskEvents,
    TemplateEvents,
    UserEvents,
    WebhookEvents,
    WorkflowEvents,
)
from src.logs.events.schema import Actor, EventObject

USERNAME_PARAM = 'username'
ADMIN_ACCOUNT_MODEL = 'accounts.account'
# Rows of the admin site the journal knows an object type for; any
# other model is OTHER and named in the payload.
ADMIN_OBJECT_TYPES: Dict[str, str] = {
    ADMIN_ACCOUNT_MODEL: EventObjectType.ACCOUNT,
    'accounts.user': EventObjectType.USER,
    'accounts.usergroup': EventObjectType.GROUP,
    'accounts.apikey': EventObjectType.API_KEY,
    'accounts.userinvite': EventObjectType.INVITE,
}


class AuditEventService:

    """ Audit events of the actions that leave no WorkflowEvent behind.

        One method per action, called from the view or the service
        where the action happens. The caller passes who acts - user
        and auth_type, the way a view reads them from the request and
        a service takes them in its constructor - and the object the
        action is about; what goes into the journal is decided here
        and nowhere else. The user becomes the actor of the record,
        the auth type is written next to it as it is: a session, an
        API key, a guest link. A user of None is the system - a
        background job, a task of the queue, a management command -
        and the record has no actor. Only the methods such a caller
        reaches accept it: the ones that take the account from the
        object instead of the user.

        The address, the browser and the request id are not passed:
        emit() reads them from the context EventContextMiddleware
        publishes for the current request.

        The model arguments are deliberately not annotated: the journal
        knows no model of any app, and importing them here only to name
        a type would turn the dependency of the apps on the journal
        around. """

    @staticmethod
    def _actor(user) -> Optional[Actor]:
        return None if user is None else Actor.from_user(user)

    @staticmethod
    def _user_object(user) -> EventObject:
        return EventObject(type=EventObjectType.USER, id=user.id)

    @classmethod
    def _event(
        cls,
        event_type: str,
        *,
        user,
        auth_type: Optional[str],
        object_type: EventObjectType.LITERALS,
        object_id: Optional[Union[int, str]] = None,
        payload: Optional[Dict[str, Any]] = None,
        workflow_id: Optional[int] = None,
        task_id: Optional[int] = None,
        account_id: Optional[int] = None,
    ) -> None:

        """ The common shape: user acts on an object of an account.
            The account is the one of the user unless the caller names
            another: a system action has no user to take it from, and
            no credential either - a service built without a user
            still carries the default auth type of its constructor,
            which says nothing about who acted. """

        emit(
            event_type,
            account_id=user.account_id if account_id is None else account_id,
            actor=cls._actor(user),
            auth_type=auth_type if user is not None else None,
            event_object=EventObject(type=object_type, id=object_id),
            payload=payload,
            workflow_id=workflow_id,
            task_id=task_id,
        )

    @classmethod
    def _user_event(
        cls,
        event_type: str,
        user,
        payload: Optional[Dict[str, Any]] = None,
        auth_type: Optional[str] = None,
    ) -> None:

        """ A person acting on themselves without an authenticated
            request: signing in, signing up, following a link from an
            e-mail. The person is both the actor and the object. A
            sign in or a sign up ends with a session, so those name
            it; a link from an e-mail carries no credential. """

        emit(
            event_type,
            account_id=user.account_id,
            actor=Actor.from_user(user),
            auth_type=auth_type,
            event_object=cls._user_object(user),
            payload=payload,
        )

    # Authentication

    @classmethod
    def user_logged_in(cls, user, source: str) -> None:
        cls._user_event(
            UserEvents.LOGIN,
            user,
            {'source': source},
            auth_type=AuthTokenType.USER,
        )

    @classmethod
    def user_signed_up(cls, user, source: str) -> None:
        cls._user_event(
            UserEvents.SIGNUP,
            user,
            {'source': source},
            auth_type=AuthTokenType.USER,
        )

    @classmethod
    def login_failed(
        cls,
        reason: LoginFailedReason.LITERALS,
        email: Optional[str],
    ) -> None:

        """ One event for every rejected attempt, so that the payload
            cannot tell an unknown address from a wrong password: both
            reach here with the same reason. The attempt is anonymous:
            no actor and no auth type. A failed sign in belongs to no
            account: NO_ACCOUNT keeps those events in a bucket of their
            own, the one an alert on a brute force burst is built on. """

        emit(
            UserEvents.LOGIN_FAILED,
            account_id=NO_ACCOUNT,
            event_object=EventObject(type=EventObjectType.USER),
            payload={
                'email': (email or '').strip().lower(),
                'reason': reason,
            },
        )

    @classmethod
    def user_logged_out(cls, user, auth_type: Optional[str]) -> None:
        cls._event(
            UserEvents.LOGOUT,
            user=user,
            auth_type=auth_type,
            object_type=EventObjectType.USER,
            object_id=user.id,
            # Not "token_type": normalize_payload treats every key
            # holding "token" as a secret and replaces its value.
            payload={'auth_type': auth_type},
        )

    @classmethod
    def user_logged_out_by_provider(cls, target, source: str) -> None:

        """ The identity provider ended the sessions, not the person:
            the actor is the system. """

        cls._event(
            UserEvents.LOGOUT,
            user=None,
            auth_type=None,
            object_type=EventObjectType.USER,
            object_id=target.id,
            payload={
                'source': source,
                'reason': LogoutReason.IDENTITY_PROVIDER,
            },
            account_id=target.account_id,
        )

    @classmethod
    def superuser_logged_in_as(cls, user, auth_type, target) -> None:
        cls._event(
            UserEvents.LOGIN_AS,
            user=user,
            auth_type=auth_type,
            object_type=EventObjectType.USER,
            object_id=target.id,
            payload={'target_email': target.email},
            account_id=target.account_id,
        )

    @classmethod
    def tenant_logged_in_as(cls, user, auth_type, tenant_account) -> None:

        """ Into the journal of the tenant: it is the account somebody
            from the master account got into. """

        cls._event(
            AccountEvents.TENANT_LOGIN_AS,
            user=user,
            auth_type=auth_type,
            object_type=EventObjectType.ACCOUNT,
            object_id=tenant_account.id,
            payload={'master_account_id': user.account_id},
            account_id=tenant_account.id,
        )

    @classmethod
    def password_reset_requested(cls, target) -> None:

        """ Somebody asked for a reset e-mail of the user. The request
            is anonymous, so the record has no actor, and the address
            the e-mail went to is the target. Only an address that
            belongs to somebody gets here: an unknown one sends no
            e-mail and leaves nothing in any account. """

        emit(
            UserEvents.PASSWORD_RESET_REQUEST,
            account_id=target.account_id,
            event_object=cls._user_object(target),
            payload={'target_email': target.email},
        )

    @classmethod
    def password_reset(cls, user) -> None:

        """ The holder of a reset link set a new password. The link
            names the person, so the person is the actor. """

        cls._user_event(UserEvents.PASSWORD_RESET, user)

    @classmethod
    def password_changed(cls, user, auth_type: Optional[str]) -> None:
        cls._event(
            UserEvents.PASSWORD_CHANGE,
            user=user,
            auth_type=auth_type,
            object_type=EventObjectType.USER,
            object_id=user.id,
        )

    @classmethod
    def password_set(cls, user, auth_type: Optional[str], target) -> None:

        """ The owner changing their own password and somebody else
            setting it are two different records: an alert watches the
            second one. """

        if user is not None and user.id == target.id:
            cls.password_changed(user, auth_type)
            return
        cls._event(
            UserEvents.PASSWORD_SET,
            user=user,
            auth_type=auth_type,
            object_type=EventObjectType.USER,
            object_id=target.id,
            payload={'target_email': target.email},
            account_id=target.account_id,
        )

    # Accounts, users, groups, invites and API keys

    @classmethod
    def user_created(cls, user, auth_type, target) -> None:

        """ An admin added a user to the account directly, without an
            invite: the sign up of an account owner is user.signup. """

        cls._event(
            UserEvents.CREATE,
            user=user,
            auth_type=auth_type,
            object_type=EventObjectType.USER,
            object_id=target.id,
            payload={
                'target_email': target.email,
                'is_admin': target.is_admin,
            },
        )

    @classmethod
    def user_updated(
        cls,
        user,
        auth_type: Optional[str],
        target,
        changed_fields: List[str],
        previous_email: str,
        group_changes: Dict[str, List[int]],
    ) -> None:

        """ One user.update naming every changed field, and apart from
            it the records an alert watches for: the admin permission
            and a password. An admin edit of the user reaches both of
            them through here, and without them a grant of admin made
            this way would not be seen by the alert. Nothing changed,
            nothing is written. """

        if not changed_fields:
            return
        payload: Dict[str, Any] = {
            'target_email': target.email,
            'changed_fields': changed_fields,
            **group_changes,
        }
        if 'email' in changed_fields:
            payload['previous_email'] = previous_email
        if 'manager' in changed_fields:
            payload['manager_id'] = target.manager_id
        cls._event(
            UserEvents.UPDATE,
            user=user,
            auth_type=auth_type,
            object_type=EventObjectType.USER,
            object_id=target.id,
            payload=payload,
            account_id=target.account_id,
        )
        if 'is_admin' in changed_fields:
            cls.user_admin_toggled(user, auth_type, target)
        if 'password' in changed_fields:
            cls.password_set(user, auth_type, target)

    @classmethod
    def user_admin_toggled(
        cls,
        user,
        auth_type: Optional[str],
        target,
    ) -> None:

        """ Granting admin is the privilege escalation the journal
            exists for: a record of its own, whichever way it was
            granted. """

        cls._event(
            UserEvents.ADMIN_TOGGLE,
            user=user,
            auth_type=auth_type,
            object_type=EventObjectType.USER,
            object_id=target.id,
            payload={
                'is_admin': target.is_admin,
                'target_email': target.email,
            },
            account_id=target.account_id,
        )

    @classmethod
    def user_deactivated(
        cls,
        user,
        auth_type: Optional[str],
        target,
        status_before: str,
    ) -> None:

        """ Every way out goes through here: the user endpoint, its
            deprecated twin, a declined invite and a transfer to
            another account. In the last two the actor is the person
            themselves. """

        cls._event(
            UserEvents.DEACTIVATE,
            user=user,
            auth_type=auth_type,
            object_type=EventObjectType.USER,
            object_id=target.id,
            payload={
                'target_email': target.email,
                'status_before': status_before,
            },
            account_id=target.account_id,
        )

    @classmethod
    def user_transferred(cls, user, auth_type, prev_user) -> None:

        """ Into the journal of the account the person moved to; the
            payload names where they came from. """

        cls._event(
            UserEvents.TRANSFER,
            user=user,
            auth_type=auth_type,
            object_type=EventObjectType.USER,
            object_id=user.id,
            payload={
                'prev_account_id': prev_user.account_id,
                'prev_user_id': prev_user.id,
            },
        )

    @classmethod
    def user_reassigned(
        cls,
        user,
        auth_type,
        old_user=None,
        new_user=None,
        old_group=None,
        new_group=None,
    ) -> None:

        """ The object is whoever hands the work over, a user or a
            group; the payload names both sides by id. One of the two is
            always there: ReassignService refuses a call without an old
            user and without an old group. """

        if old_user is not None:
            object_type, object_id = EventObjectType.USER, old_user.id
        else:
            object_type, object_id = EventObjectType.GROUP, old_group.id
        cls._event(
            UserEvents.REASSIGN,
            user=user,
            auth_type=auth_type,
            object_type=object_type,
            object_id=object_id,
            payload={
                'old_user_id': old_user.id if old_user else None,
                'old_group_id': old_group.id if old_group else None,
                'new_user_id': new_user.id if new_user else None,
                'new_group_id': new_group.id if new_group else None,
            },
        )

    @classmethod
    def user_unsubscribed(cls, user, email_type: str) -> None:

        """ The link in the e-mail names the person, and the request
            carries no authentication: the person is the actor. """

        cls._user_event(
            UserEvents.UNSUBSCRIBE,
            user,
            {'email_type': email_type},
        )

    @classmethod
    def vacation_activated(
        cls,
        user,
        auth_type: Optional[str],
        target,
        substitute_user_ids: List[int],
        absence_status: str,
        start_date: Optional[date],
        end_date: Optional[date],
        delegated_tasks_count: int,
        is_update: bool,
    ) -> None:

        """ target is the person on vacation, user whoever turns it on:
            the person themselves, an admin, or nobody for a scheduled
            task. """

        cls._event(
            UserEvents.VACATION_ACTIVATE,
            user=user,
            auth_type=auth_type,
            object_type=EventObjectType.USER,
            object_id=target.id,
            payload={
                'target_email': target.email,
                'substitute_user_ids': sorted(substitute_user_ids),
                'absence_status': absence_status,
                'start_date': start_date,
                'end_date': end_date,
                'delegated_tasks_count': delegated_tasks_count,
                'is_update': is_update,
            },
            account_id=target.account_id,
        )

    @classmethod
    def vacation_deactivated(
        cls,
        user,
        auth_type: Optional[str],
        target,
    ) -> None:
        cls._event(
            UserEvents.VACATION_DEACTIVATE,
            user=user,
            auth_type=auth_type,
            object_type=EventObjectType.USER,
            object_id=target.id,
            payload={'target_email': target.email},
            account_id=target.account_id,
        )

    @classmethod
    def account_updated(
        cls,
        user,
        auth_type,
        account,
        changed_fields: List[str],
    ) -> None:

        """ Names of the fields only: the values are the name and the
            logos of the company, and the account itself keeps them. """

        cls._event(
            AccountEvents.UPDATE,
            user=user,
            auth_type=auth_type,
            object_type=EventObjectType.ACCOUNT,
            object_id=account.id,
            payload={'changed_fields': changed_fields},
        )

    @classmethod
    def account_verified(cls, user) -> None:

        """ The link carries no authentication: it names the person it
            was sent to, so the person is the actor. """

        emit(
            AccountEvents.VERIFY,
            account_id=user.account_id,
            actor=Actor.from_user(user),
            event_object=EventObject(
                type=EventObjectType.ACCOUNT, id=user.account_id,
            ),
        )

    @classmethod
    def verification_resent(cls, user, auth_type, account_owner) -> None:
        cls._event(
            AccountEvents.VERIFICATION_RESEND,
            user=user,
            auth_type=auth_type,
            object_type=EventObjectType.ACCOUNT,
            object_id=account_owner.account_id,
            payload={'target_email': account_owner.email},
        )

    @classmethod
    def _tenant_event(cls, event_type: str, user, auth_type, tenant) -> None:

        """ Into the master account: the tenant is what the master
            account did, and a deleted tenant has no journal of its own
            to look in. """

        cls._event(
            event_type,
            user=user,
            auth_type=auth_type,
            object_type=EventObjectType.ACCOUNT,
            object_id=tenant.id,
            payload={
                'name': tenant.tenant_name,
                'billing_plan': tenant.billing_plan,
            },
        )

    @classmethod
    def tenant_created(cls, user, auth_type, tenant) -> None:
        cls._tenant_event(AccountEvents.TENANT_CREATE, user, auth_type, tenant)

    @classmethod
    def tenant_deleted(cls, user, auth_type, tenant) -> None:
        cls._tenant_event(AccountEvents.TENANT_DELETE, user, auth_type, tenant)

    @classmethod
    def _invite_event(
        cls,
        event_type: str,
        user,
        auth_type,
        invited_user,
        is_transfer: bool,
    ) -> None:

        """ Who was invited, and whether the person already works in
            another account: then the e-mail offers a transfer instead
            of a sign up.

            No object id: the id of an invite is the key that accepts
            it, the accept endpoint asks for nothing else, and the
            journal leaves the deployment. """

        cls._event(
            event_type,
            user=user,
            auth_type=auth_type,
            object_type=EventObjectType.INVITE,
            payload={
                'target_email': invited_user.email,
                'invited_user_id': invited_user.id,
                'is_transfer': is_transfer,
            },
        )

    @classmethod
    def invite_created(
        cls,
        user,
        auth_type,
        invited_user,
        is_transfer: bool,
    ) -> None:
        cls._invite_event(
            UserEvents.INVITE_CREATE,
            user,
            auth_type,
            invited_user,
            is_transfer,
        )

    @classmethod
    def invite_resent(
        cls,
        user,
        auth_type,
        invited_user,
        is_transfer: bool,
    ) -> None:
        cls._invite_event(
            UserEvents.INVITE_RESEND,
            user,
            auth_type,
            invited_user,
            is_transfer,
        )

    @classmethod
    def invite_accepted(cls, invited_user, invited_by_id: int) -> None:

        """ The invited person is the actor: accepting is what they
            did, whether through the endpoint or an SSO callback. """

        cls._event(
            UserEvents.INVITE_ACCEPT,
            user=invited_user,
            auth_type=None,
            object_type=EventObjectType.INVITE,
            payload={'invited_by_id': invited_by_id},
        )

    @classmethod
    def _group_event(
        cls,
        event_type: str,
        user,
        auth_type,
        group,
        payload: Dict[str, Any],
    ) -> None:
        cls._event(
            event_type,
            user=user,
            auth_type=auth_type,
            object_type=EventObjectType.GROUP,
            object_id=group.id,
            payload=payload,
            account_id=group.account_id,
        )

    @classmethod
    def group_created(
        cls,
        user,
        auth_type,
        group,
        users_ids: List[int],
    ) -> None:
        cls._group_event(
            GroupEvents.CREATE,
            user,
            auth_type,
            group,
            payload={'name': group.name, 'users_ids': users_ids},
        )

    @classmethod
    def group_updated(
        cls,
        user,
        auth_type,
        group,
        changed_fields: List[str],
        added_users_ids: List[int],
        removed_users_ids: List[int],
    ) -> None:

        """ Nothing changed, nothing is written. """

        if not changed_fields:
            return
        cls._group_event(
            GroupEvents.UPDATE,
            user,
            auth_type,
            group,
            payload={
                'changed_fields': sorted(changed_fields),
                'added_users_ids': added_users_ids,
                'removed_users_ids': removed_users_ids,
            },
        )

    @classmethod
    def group_deleted(
        cls,
        user,
        auth_type,
        group,
        users_ids: List[int],
    ) -> None:
        cls._group_event(
            GroupEvents.DELETE,
            user,
            auth_type,
            group,
            payload={'name': group.name, 'users_ids': users_ids},
        )

    @classmethod
    def _api_key_event(cls, event_type: str, user, auth_type, api_key) -> None:

        """ The payload names the key and its owner and nothing else.
            Neither the raw key nor api_key.token may be put here: the
            journal leaves the deployment, and a key that reaches a log
            backend is a key an operator can sign in with. """

        cls._event(
            event_type,
            user=user,
            auth_type=auth_type,
            object_type=EventObjectType.API_KEY,
            object_id=api_key.id,
            payload={
                'name': api_key.name,
                'target_user_id': api_key.user_id,
            },
            account_id=api_key.account_id,
        )

    @classmethod
    def api_key_created(cls, user, auth_type, api_key) -> None:
        cls._api_key_event(ApiKeyEvents.CREATE, user, auth_type, api_key)

    @classmethod
    def api_key_revoked(cls, user, auth_type, api_key) -> None:
        cls._api_key_event(ApiKeyEvents.REVOKE, user, auth_type, api_key)

    # Django admin site: a superuser editing the rows directly

    @classmethod
    def _admin_event(
        cls,
        event_type: str,
        user,
        target,
        model: str,
        changes: Optional[Dict[str, Any]] = None,
    ) -> None:

        """ Into the account the row belongs to, so that the account
            sees what a superuser did to it: an account row is its own
            account, a row of no account (a product, a system message)
            goes to the account of the superuser. No object id for an
            invite: its id is the key that accepts it. """

        object_type = ADMIN_OBJECT_TYPES.get(model, EventObjectType.OTHER)
        if model == ADMIN_ACCOUNT_MODEL:
            account_id = target.id
        else:
            account_id = getattr(target, 'account_id', None)
        cls._event(
            event_type,
            user=user,
            auth_type=None,
            object_type=object_type,
            object_id=(
                None if object_type == EventObjectType.INVITE else target.pk
            ),
            payload={'model': model, **(changes or {})},
            account_id=account_id,
        )

    @classmethod
    def admin_created(
        cls,
        user,
        target,
        model: str,
        changes: Optional[Dict[str, Any]] = None,
    ) -> None:
        cls._admin_event(AdminEvents.CREATE, user, target, model, changes)

    @classmethod
    def admin_updated(
        cls,
        user,
        target,
        model: str,
        changes: Optional[Dict[str, Any]] = None,
    ) -> None:
        cls._admin_event(AdminEvents.UPDATE, user, target, model, changes)

    @classmethod
    def admin_deleted(cls, user, target, model: str) -> None:
        cls._admin_event(AdminEvents.DELETE, user, target, model)

    # Billing

    @classmethod
    def purchase_made(
        cls,
        user,
        auth_type,
        products: List[Dict[str, Any]],
    ) -> None:

        """ The products are a mapping of the price code to the
            quantity, not a list of objects: normalize_payload turns a
            container nested that deep into one JSON string. A code sent
            twice is one key holding the sum, the way Stripe is asked
            for it. """

        quantity_by_code: Dict[str, int] = {}
        for product in products:
            code = product['code']
            quantity_by_code[code] = (
                quantity_by_code.get(code, 0) + product['quantity']
            )
        cls._event(
            BillingEvents.PURCHASE,
            user=user,
            auth_type=auth_type,
            object_type=EventObjectType.ACCOUNT,
            object_id=user.account_id,
            payload={'products': quantity_by_code},
        )

    @classmethod
    def subscription_cancelled(cls, user, auth_type) -> None:
        cls._event(
            BillingEvents.SUBSCRIPTION_CANCEL,
            user=user,
            auth_type=auth_type,
            object_type=EventObjectType.ACCOUNT,
            object_id=user.account_id,
        )

    @classmethod
    def payment_confirmed(
        cls,
        user,
        auth_type: Optional[str],
        subscription_data: Optional[Dict[str, Any]],
    ) -> None:

        """ The confirmation link is signed for the user who started the
            payment: the actor is that user, whoever follows the link. """

        payload = {}
        if subscription_data:
            payload = {
                'billing_plan': subscription_data.get('billing_plan'),
                'max_users': subscription_data.get('max_users'),
            }
        cls._event(
            BillingEvents.PAYMENT_CONFIRM,
            user=user,
            auth_type=auth_type,
            object_type=EventObjectType.ACCOUNT,
            object_id=user.account_id,
            payload=payload,
        )

    # Webhooks

    @classmethod
    def _webhook_event(
        cls,
        event_type: str,
        user,
        auth_type,
        url: str,
        event: str,
    ) -> None:

        """ Who pointed which address at which event, the two
            questions the journal has to answer about a webhook.
            normalize_payload cuts the query string off the address:
            a receiver token rides there, and the host with the path
            is what identifies the destination. """

        cls._event(
            event_type,
            user=user,
            auth_type=auth_type,
            object_type=EventObjectType.WEBHOOK,
            payload={'url': url, 'event': event},
        )

    @classmethod
    def webhook_subscribed(cls, user, auth_type, url: str, event: str) -> None:
        cls._webhook_event(
            WebhookEvents.SUBSCRIBE, user, auth_type, url, event,
        )

    @classmethod
    def webhook_unsubscribed(
        cls,
        user,
        auth_type,
        url: str,
        event: str,
    ) -> None:
        cls._webhook_event(
            WebhookEvents.UNSUBSCRIBE, user, auth_type, url, event,
        )

    # Templates

    @classmethod
    def _template_event(
        cls,
        event_type: str,
        user,
        auth_type,
        template,
        name: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        cls._event(
            event_type,
            user=user,
            auth_type=auth_type,
            object_type=EventObjectType.TEMPLATE,
            object_id=template.id,
            payload={
                'name': name,
                'version': template.version,
                'is_active': template.is_active,
                **(extra or {}),
            },
        )

    @classmethod
    def template_saved(
        cls,
        user,
        auth_type,
        template,
        name: str,
        source: Optional[str] = None,
    ) -> None:

        """ A published template is an audit record, a draft is not:
            the type follows the state the template ended up in. The
            name comes from the caller: for a draft it lives in the
            draft, not in the template row.

            source names a way of creating the template other than the
            editor: steps typed in one form or a library template. """

        cls._template_event(
            TemplateEvents.PUBLISH if template.is_active
            else TemplateEvents.DRAFT_SAVE,
            user,
            auth_type,
            template,
            name=name,
            extra={'source': source} if source else None,
        )

    @classmethod
    def template_cloned(cls, user, auth_type, template, name: str) -> None:
        cls._template_event(
            TemplateEvents.CLONE, user, auth_type, template, name=name,
        )

    @classmethod
    def template_deleted(cls, user, auth_type, template) -> None:
        cls._template_event(
            TemplateEvents.DELETE,
            user,
            auth_type,
            template,
            name=template.name,
        )

    @classmethod
    def templates_exported(
        cls,
        user,
        auth_type,
        filters: Dict[str, Any],
    ) -> None:

        """ No object id: the export is a bulk read, the filters say
            what left the account. """

        cls._event(
            TemplateEvents.EXPORT,
            user=user,
            auth_type=auth_type,
            object_type=EventObjectType.TEMPLATE,
            payload={'filters': filters},
        )

    @classmethod
    def template_draft_discarded(
        cls,
        user,
        auth_type,
        template,
        template_deleted: bool,
    ) -> None:

        """ A template that was never published has nothing to go back
            to: discarding its draft deletes the template itself. """

        cls._template_event(
            TemplateEvents.DRAFT_DISCARD,
            user,
            auth_type,
            template,
            name=template.name,
            extra={'template_deleted': template_deleted},
        )

    @classmethod
    def template_generated_with_ai(cls, user, auth_type) -> None:

        """ No payload: the description is text the user typed, and the
            generated template is not saved until the user saves it. """

        cls._event(
            TemplateEvents.AI_GENERATE,
            user=user,
            auth_type=auth_type,
            object_type=EventObjectType.TEMPLATE,
        )

    @classmethod
    def template_filled_from_library(
        cls,
        user,
        auth_type,
        system_template,
    ) -> None:
        cls._event(
            TemplateEvents.LIBRARY_FILL,
            user=user,
            auth_type=auth_type,
            object_type=EventObjectType.SYSTEM_TEMPLATE,
            object_id=system_template.id,
            payload={'name': system_template.name},
        )

    @classmethod
    def library_templates_imported(
        cls,
        user,
        auth_type,
        templates_count: int,
    ) -> None:
        cls._event(
            TemplateEvents.LIBRARY_IMPORT,
            user=user,
            auth_type=auth_type,
            object_type=EventObjectType.SYSTEM_TEMPLATE,
            payload={'templates_count': templates_count},
        )

    @classmethod
    def _template_preset_event(
        cls,
        event_type: str,
        user,
        auth_type,
        preset,
    ) -> None:
        cls._event(
            event_type,
            user=user,
            auth_type=auth_type,
            object_type=EventObjectType.TEMPLATE_PRESET,
            object_id=preset.id,
            payload={
                'name': preset.name,
                'template_id': preset.template_id,
                'type': preset.type,
                'is_default': preset.is_default,
            },
        )

    @classmethod
    def template_preset_created(cls, user, auth_type, preset) -> None:
        cls._template_preset_event(
            TemplateEvents.PRESET_CREATE, user, auth_type, preset,
        )

    @classmethod
    def template_preset_updated(cls, user, auth_type, preset) -> None:
        cls._template_preset_event(
            TemplateEvents.PRESET_UPDATE, user, auth_type, preset,
        )

    @classmethod
    def template_preset_deleted(cls, user, auth_type, preset) -> None:
        cls._template_preset_event(
            TemplateEvents.PRESET_DELETE, user, auth_type, preset,
        )

    @classmethod
    def template_preset_set_default(cls, user, auth_type, preset) -> None:
        cls._template_preset_event(
            TemplateEvents.PRESET_SET_DEFAULT, user, auth_type, preset,
        )

    # Fieldsets and datasets

    @classmethod
    def _named_object_event(
        cls,
        event_type: str,
        user,
        auth_type,
        object_type: EventObjectType.LITERALS,
        object_id: int,
        name: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:

        """ A fieldset or a dataset: names and counts only, the values
            of the fields and the rows are the data of the customer, and
            the object itself keeps them. """

        cls._event(
            event_type,
            user=user,
            auth_type=auth_type,
            object_type=object_type,
            object_id=object_id,
            payload={'name': name, **(extra or {})},
        )

    @classmethod
    def fieldset_created(cls, user, auth_type, fieldset) -> None:
        cls._named_object_event(
            TemplateEvents.FIELDSET_CREATE,
            user,
            auth_type,
            object_type=EventObjectType.FIELDSET,
            object_id=fieldset.id,
            name=fieldset.name,
        )

    @classmethod
    def fieldset_updated(cls, user, auth_type, fieldset) -> None:
        cls._named_object_event(
            TemplateEvents.FIELDSET_UPDATE,
            user,
            auth_type,
            object_type=EventObjectType.FIELDSET,
            object_id=fieldset.id,
            name=fieldset.name,
        )

    @classmethod
    def fieldset_cloned(
        cls,
        user,
        auth_type,
        clone,
        source_fieldset_id: int,
    ) -> None:
        cls._named_object_event(
            TemplateEvents.FIELDSET_CLONE,
            user,
            auth_type,
            object_type=EventObjectType.FIELDSET,
            object_id=clone.id,
            name=clone.name,
            extra={'source_fieldset_id': source_fieldset_id},
        )

    @classmethod
    def fieldset_deleted(cls, user, auth_type, fieldset) -> None:
        cls._named_object_event(
            TemplateEvents.FIELDSET_DELETE,
            user,
            auth_type,
            object_type=EventObjectType.FIELDSET,
            object_id=fieldset.id,
            name=fieldset.name,
        )

    @classmethod
    def dataset_created(
        cls,
        user,
        auth_type,
        dataset,
        items_count: int,
    ) -> None:
        cls._named_object_event(
            DatasetEvents.CREATE,
            user,
            auth_type,
            object_type=EventObjectType.DATASET,
            object_id=dataset.id,
            name=dataset.name,
            extra={'items_count': items_count},
        )

    @classmethod
    def dataset_updated(
        cls,
        user,
        auth_type,
        dataset,
        changed_fields: List[str],
    ) -> None:
        cls._named_object_event(
            DatasetEvents.UPDATE,
            user,
            auth_type,
            object_type=EventObjectType.DATASET,
            object_id=dataset.id,
            name=dataset.name,
            extra={'changed_fields': changed_fields},
        )

    @classmethod
    def dataset_deleted(cls, user, auth_type, dataset) -> None:
        cls._named_object_event(
            DatasetEvents.DELETE,
            user,
            auth_type,
            object_type=EventObjectType.DATASET,
            object_id=dataset.id,
            name=dataset.name,
        )

    @classmethod
    def dataset_items_added(
        cls,
        user,
        auth_type,
        dataset,
        items_count: int,
    ) -> None:
        cls._named_object_event(
            DatasetEvents.ITEMS_ADD,
            user,
            auth_type,
            object_type=EventObjectType.DATASET,
            object_id=dataset.id,
            name=dataset.name,
            extra={'items_count': items_count},
        )

    @classmethod
    def dataset_items_replaced(
        cls,
        user,
        auth_type,
        dataset,
        items_count: int,
    ) -> None:
        cls._named_object_event(
            DatasetEvents.ITEMS_REPLACE,
            user,
            auth_type,
            object_type=EventObjectType.DATASET,
            object_id=dataset.id,
            name=dataset.name,
            extra={'items_count': items_count},
        )

    @classmethod
    def _dataset_item_event(
        cls,
        event_type: str,
        user,
        auth_type,
        item,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        cls._event(
            event_type,
            user=user,
            auth_type=auth_type,
            object_type=EventObjectType.DATASET_ITEM,
            object_id=item.id,
            payload={'dataset_id': item.dataset_id, **(extra or {})},
        )

    @classmethod
    def dataset_item_created(cls, user, auth_type, item) -> None:
        cls._dataset_item_event(
            DatasetEvents.ITEM_CREATE, user, auth_type, item,
        )

    @classmethod
    def dataset_item_updated(
        cls,
        user,
        auth_type,
        item,
        changed_fields: List[str],
    ) -> None:
        cls._dataset_item_event(
            DatasetEvents.ITEM_UPDATE,
            user,
            auth_type,
            item,
            extra={'changed_fields': changed_fields},
        )

    @classmethod
    def dataset_item_deleted(cls, user, auth_type, item) -> None:
        cls._dataset_item_event(
            DatasetEvents.ITEM_DELETE, user, auth_type, item,
        )

    # Workflows and tasks changed in place

    @classmethod
    def workflow_updated(
        cls,
        user,
        auth_type,
        workflow,
        changed_fields: List[str],
        kickoff_fields: List[str],
    ) -> None:

        """ The api names of the kickoff fields the request sent, not
            their values: those are the data of the customer, and the
            workflow keeps them. The urgent mark has its own record from
            the workflow event, it is only named among the fields here. """

        payload: Dict[str, Any] = {
            'workflow_name': workflow.name,
            'changed_fields': changed_fields,
        }
        if kickoff_fields:
            payload['kickoff_fields'] = kickoff_fields
        cls._event(
            WorkflowEvents.UPDATE,
            user=user,
            auth_type=auth_type,
            object_type=EventObjectType.WORKFLOW,
            object_id=workflow.id,
            payload=payload,
            workflow_id=workflow.id,
        )

    @classmethod
    def workflow_terminated(cls, user, auth_type, workflow) -> None:

        """ The only workflow action that leaves no WorkflowEvent
            behind. Published after the delete: a delete that fails
            raises before it, and the delete is a soft one, so the name
            and the template are still there. """

        cls._event(
            WorkflowEvents.TERMINATE,
            user=user,
            auth_type=auth_type,
            object_type=EventObjectType.WORKFLOW,
            object_id=workflow.id,
            payload={
                'workflow_name': workflow.name,
                'template_id': workflow.template_id,
            },
            workflow_id=workflow.id,
            account_id=workflow.account_id,
        )

    @classmethod
    def _comment_event(cls, event_type: str, user, auth_type, comment) -> None:

        """ No text, neither the old nor the new one: a comment is the
            content of the customer, and the workflow event keeps it.
            With the journal off nothing is read: the workflow and the
            task each cost a query. """

        if not logs_enabled():
            return
        payload = {'workflow_name': comment.workflow.name}
        if comment.task is not None:
            payload['task_name'] = comment.task.name
        cls._event(
            event_type,
            user=user,
            auth_type=auth_type,
            object_type=EventObjectType.COMMENT,
            object_id=comment.id,
            payload=payload,
            workflow_id=comment.workflow_id,
            task_id=comment.task_id,
        )

    @classmethod
    def comment_updated(cls, user, auth_type, comment) -> None:
        cls._comment_event(
            TaskEvents.COMMENT_UPDATE, user, auth_type, comment,
        )

    @classmethod
    def comment_deleted(cls, user, auth_type, comment) -> None:
        cls._comment_event(
            TaskEvents.COMMENT_DELETE, user, auth_type, comment,
        )

    @classmethod
    def _checklist_event(
        cls,
        event_type: str,
        user,
        auth_type,
        checklist,
        selection_id: int,
    ) -> None:
        if not logs_enabled():
            return
        task = checklist.task
        cls._event(
            event_type,
            user=user,
            auth_type=auth_type,
            object_type=EventObjectType.CHECKLIST,
            object_id=checklist.id,
            payload={
                'workflow_name': task.workflow.name,
                'task_name': task.name,
                'checklist_api_name': checklist.api_name,
                'selection_id': selection_id,
            },
            workflow_id=task.workflow_id,
            task_id=task.id,
        )

    @classmethod
    def checklist_item_marked(
        cls,
        user,
        auth_type,
        checklist,
        selection_id: int,
    ) -> None:
        cls._checklist_event(
            TaskEvents.CHECKLIST_MARK,
            user,
            auth_type,
            checklist,
            selection_id=selection_id,
        )

    @classmethod
    def checklist_item_unmarked(
        cls,
        user,
        auth_type,
        checklist,
        selection_id: int,
    ) -> None:
        cls._checklist_event(
            TaskEvents.CHECKLIST_UNMARK,
            user,
            auth_type,
            checklist,
            selection_id=selection_id,
        )
