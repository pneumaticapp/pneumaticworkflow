from hashlib import sha256
from typing import Any, Dict, List, Optional

from src.logs.events.emitter import NO_ACCOUNT, emit
from src.logs.events.enums import (
    ActorType,
    EventName,
    EventObjectType,
)
from src.logs.events.schema import Actor, EventObject

USERNAME_PARAM = 'username'


class AuditEventService:

    """ Audit events of the actions that leave no WorkflowEvent behind.

        A view calls one method here and stays free of the details:
        which type the action is, what its object is and which of its
        data belongs in the journal. The workflow events reach the
        stream through WorkflowEventService instead. """

    @staticmethod
    def _actor(request) -> Actor:
        return Actor.from_user(request.user, request.token_type)

    @staticmethod
    def _user_object(user) -> EventObject:
        return EventObject(type=EventObjectType.USER, id=user.id)

    @staticmethod
    def _email_hash(value: Any) -> str:

        """ Hash of a normalized address, the only form a sign in
            address is allowed to take in a failed attempt event: a
            raw address of a person who never signed in is personal
            data the product has no reason to keep. """

        normalized = str(value or '').strip().lower()
        return sha256(normalized.encode('utf-8')).hexdigest()

    @classmethod
    def _user_event(
        cls,
        event_type: str,
        user,
        source: str,
        request=None,
    ) -> None:

        """ A person signing in or signing up: the person is both the
            actor and the object, and the source names the provider. """

        emit(
            event_type,
            account_id=user.account_id,
            actor=Actor.from_user(user),
            event_object=cls._user_object(user),
            payload={'source': source},
            request=request,
        )

    @classmethod
    def user_logged_in(cls, user, source: str, request=None) -> None:
        cls._user_event(
            EventName.USER_LOGIN,
            user=user,
            source=source,
            request=request,
        )

    @classmethod
    def user_signed_up(cls, user, source: str, request=None) -> None:
        cls._user_event(
            EventName.USER_SIGNUP,
            user=user,
            source=source,
            request=request,
        )

    @classmethod
    def login_failed(
        cls,
        request,
        reason: str,
        email: Optional[str] = None,
    ) -> None:

        """ One event for every rejected attempt, so that the payload
            cannot tell an unknown address from a wrong password: both
            reach here with the same reason, and the address is present
            as a hash only. A password sign in carries the address in
            the request body, an SSO callback in the provider profile:
            the caller passes it when the body has none. A failed sign
            in belongs to no account: NO_ACCOUNT keeps those events in
            a bucket of their own, the one an alert on a brute force
            burst is built on. """

        if email is None:
            email = request.data.get(USERNAME_PARAM)
        emit(
            EventName.USER_LOGIN_FAILED,
            account_id=NO_ACCOUNT,
            actor=Actor(type=ActorType.GUEST),
            event_object=EventObject(type=EventObjectType.USER),
            payload={
                'email_hash': cls._email_hash(email),
                'reason': reason,
            },
            request=request,
        )

    @classmethod
    def user_logged_out(cls, request) -> None:
        emit(
            EventName.USER_LOGOUT,
            account_id=request.user.account_id,
            actor=cls._actor(request),
            event_object=cls._user_object(request.user),
            # Not "token_type": normalize_payload treats every key
            # holding "token" as a secret and replaces its value.
            payload={'auth_type': request.token_type},
            request=request,
        )

    @classmethod
    def password_reset_requested(cls, request, user) -> None:

        """ Somebody asked for a reset e-mail of the user. The request
            is anonymous, so the actor is a guest and the address the
            e-mail went to is the target. Only an address that belongs
            to somebody gets here: an unknown one sends no e-mail and
            leaves nothing in any account. """

        emit(
            EventName.USER_PASSWORD_RESET_REQUEST,
            account_id=user.account_id,
            actor=Actor(type=ActorType.GUEST),
            event_object=cls._user_object(user),
            payload={'target_email': user.email},
            request=request,
        )

    @classmethod
    def password_reset(cls, request, user) -> None:

        """ The holder of a reset link set a new password. The request
            carries no authentication: the link names the person, so
            the person is the actor. """

        emit(
            EventName.USER_PASSWORD_RESET,
            account_id=user.account_id,
            actor=Actor.from_user(user),
            event_object=cls._user_object(user),
            request=request,
        )

    @classmethod
    def password_changed(cls, request) -> None:
        emit(
            EventName.USER_PASSWORD_CHANGE,
            account_id=request.user.account_id,
            actor=cls._actor(request),
            event_object=cls._user_object(request.user),
            request=request,
        )

    @classmethod
    def user_created(cls, request, user) -> None:

        """ An admin added a user to the account directly, without an
            invite: the sign up of an account owner is user.signup. """

        emit(
            EventName.USER_CREATE,
            account_id=user.account_id,
            actor=cls._actor(request),
            event_object=cls._user_object(user),
            payload={
                'target_email': user.email,
                'is_admin': user.is_admin,
            },
            request=request,
        )

    @classmethod
    def account_updated(
        cls,
        request,
        account,
        changed_fields: List[str],
    ) -> None:

        """ Names of the fields only: the values are the name and the
            logos of the company, and the account itself keeps them. """

        emit(
            EventName.ACCOUNT_UPDATE,
            account_id=account.id,
            actor=cls._actor(request),
            event_object=EventObject(
                type=EventObjectType.ACCOUNT, id=account.id,
            ),
            payload={'changed_fields': changed_fields},
            request=request,
        )

    @classmethod
    def superuser_logged_in_as(
        cls,
        request,
        user,
        reason: Optional[str],
    ) -> None:
        emit(
            EventName.USER_LOGIN_AS,
            account_id=user.account_id,
            actor=cls._actor(request),
            event_object=cls._user_object(user),
            payload={
                'target_email': user.email,
                'reason': reason,
            },
            request=request,
        )

    @classmethod
    def tenant_logged_in_as(
        cls,
        master_user,
        tenant_account,
        auth_type: str,
    ) -> None:

        """ The request is not passed: the call comes from a service,
            and emit() takes the address and the browser from the
            context the middleware published for the same request. """

        emit(
            EventName.TENANT_LOGIN_AS,
            account_id=tenant_account.id,
            actor=Actor.from_user(master_user, auth_type),
            event_object=EventObject(
                type=EventObjectType.ACCOUNT, id=tenant_account.id,
            ),
            payload={'master_account_id': master_user.account_id},
        )

    @classmethod
    def _template_event(
        cls,
        event_type: str,
        request,
        template,
        name: str,
    ) -> None:
        emit(
            event_type,
            account_id=request.user.account_id,
            actor=cls._actor(request),
            event_object=EventObject(
                type=EventObjectType.TEMPLATE, id=template.id,
            ),
            payload={
                'name': name,
                'version': template.version,
                'is_active': template.is_active,
            },
            request=request,
        )

    @classmethod
    def template_saved(cls, request, template, name: str) -> None:

        """ A published template is an audit record, a draft is not:
            the type follows the state the template ended up in. The
            name comes from the caller: for a draft it lives in the
            draft, not in the template row. """

        cls._template_event(
            EventName.TEMPLATE_PUBLISH if template.is_active
            else EventName.TEMPLATE_DRAFT_SAVE,
            request=request,
            template=template,
            name=name,
        )

    @classmethod
    def template_cloned(cls, request, template, name: str) -> None:
        cls._template_event(
            EventName.TEMPLATE_CLONE,
            request=request,
            template=template,
            name=name,
        )

    @classmethod
    def template_deleted(cls, request, template) -> None:
        cls._template_event(
            EventName.TEMPLATE_DELETE,
            request=request,
            template=template,
            name=template.name,
        )

    @classmethod
    def templates_exported(cls, request, filters: Dict[str, Any]) -> None:

        """ No object id: the export is a bulk read, the filters say
            what left the account. """

        emit(
            EventName.TEMPLATE_EXPORT,
            account_id=request.user.account_id,
            actor=cls._actor(request),
            event_object=EventObject(type=EventObjectType.TEMPLATE),
            payload={'filters': filters},
            request=request,
        )
