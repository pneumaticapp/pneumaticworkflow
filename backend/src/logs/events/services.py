from hashlib import sha256
from typing import Any, Dict, List, Optional, Union

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
        stream through WorkflowEventService instead.

        The model arguments are deliberately not annotated: the journal
        knows no model of any app, and importing them here only to name
        a type would turn the dependency of the apps on the journal
        around. """

    @staticmethod
    def _actor(request) -> Actor:
        return Actor.from_user(request.user, request.token_type)

    @staticmethod
    def _user_object(user) -> EventObject:
        return EventObject(type=EventObjectType.USER, id=user.id)

    @classmethod
    def _request_event(
        cls,
        event_type: str,
        request,
        object_type: str,
        object_id: Optional[Union[int, str]] = None,
        payload: Optional[Dict[str, Any]] = None,
        workflow_id: Optional[int] = None,
        task_id: Optional[int] = None,
    ) -> None:

        """ The common shape: the authenticated user of the request
            acts on an object of their own account. """

        emit(
            event_type,
            account_id=request.user.account_id,
            actor=cls._actor(request),
            event_object=EventObject(type=object_type, id=object_id),
            payload=payload,
            workflow_id=workflow_id,
            task_id=task_id,
            request=request,
        )

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
    def _template_event(
        cls,
        event_type: str,
        request,
        template,
        name: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        cls._request_event(
            event_type,
            request=request,
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
    def _template_preset_event(
        cls,
        event_type: str,
        request,
        preset,
    ) -> None:
        cls._request_event(
            event_type,
            request=request,
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
    def _fieldset_event(
        cls,
        event_type: str,
        request,
        fieldset_id: int,
        name: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        cls._request_event(
            event_type,
            request=request,
            object_type=EventObjectType.FIELDSET,
            object_id=fieldset_id,
            payload={'name': name, **(extra or {})},
        )

    @classmethod
    def _dataset_event(
        cls,
        event_type: str,
        request,
        dataset_id: int,
        name: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:

        """ Names and counts only: the values of the rows are the data
            of the customer, and the dataset itself keeps them. """

        cls._request_event(
            event_type,
            request=request,
            object_type=EventObjectType.DATASET,
            object_id=dataset_id,
            payload={'name': name, **(extra or {})},
        )

    @classmethod
    def _dataset_item_event(
        cls,
        event_type: str,
        request,
        item_id: int,
        dataset_id: int,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        cls._request_event(
            event_type,
            request=request,
            object_type=EventObjectType.DATASET_ITEM,
            object_id=item_id,
            payload={'dataset_id': dataset_id, **(extra or {})},
        )

    @classmethod
    def _comment_event(cls, event_type: str, request, comment) -> None:

        """ No text, neither the old nor the new one: a comment is the
            content of the customer, and the workflow event keeps it. """

        payload = {'workflow_name': comment.workflow.name}
        if comment.task is not None:
            payload['task_name'] = comment.task.name
        cls._request_event(
            event_type,
            request=request,
            object_type=EventObjectType.COMMENT,
            object_id=comment.id,
            payload=payload,
            workflow_id=comment.workflow_id,
            task_id=comment.task_id,
        )

    @classmethod
    def _checklist_event(
        cls,
        event_type: str,
        request,
        checklist,
        selection_id: int,
    ) -> None:
        task = checklist.task
        cls._request_event(
            event_type,
            request=request,
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
    def _tenant_event(cls, event_type: str, request, tenant) -> None:

        """ Into the master account: the tenant is what the master
            account did, and a deleted tenant has no journal of its own
            to look in. """

        cls._request_event(
            event_type,
            request=request,
            object_type=EventObjectType.ACCOUNT,
            object_id=tenant.id,
            payload={
                'name': tenant.tenant_name,
                'billing_plan': tenant.billing_plan,
            },
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
        cls._request_event(
            EventName.USER_LOGOUT,
            request=request,
            object_type=EventObjectType.USER,
            object_id=request.user.id,
            # Not "token_type": normalize_payload treats every key
            # holding "token" as a secret and replaces its value.
            payload={'auth_type': request.token_type},
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
        cls._request_event(
            EventName.USER_PASSWORD_CHANGE,
            request=request,
            object_type=EventObjectType.USER,
            object_id=request.user.id,
        )

    @classmethod
    def user_created(cls, request, user) -> None:

        """ An admin added a user to the account directly, without an
            invite: the sign up of an account owner is user.signup. """

        cls._request_event(
            EventName.USER_CREATE,
            request=request,
            object_type=EventObjectType.USER,
            object_id=user.id,
            payload={
                'target_email': user.email,
                'is_admin': user.is_admin,
            },
        )

    @classmethod
    def user_reassigned(
        cls,
        request,
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
        cls._request_event(
            EventName.USER_REASSIGN,
            request=request,
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
    def user_unsubscribed(cls, request, user, email_type: str) -> None:

        """ The link in the e-mail names the person, and the request
            carries no authentication: the person is the actor. """

        emit(
            EventName.USER_UNSUBSCRIBE,
            account_id=user.account_id,
            actor=Actor.from_user(user),
            event_object=cls._user_object(user),
            payload={'email_type': email_type},
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

        cls._request_event(
            EventName.ACCOUNT_UPDATE,
            request=request,
            object_type=EventObjectType.ACCOUNT,
            object_id=account.id,
            payload={'changed_fields': changed_fields},
        )

    @classmethod
    def account_verified(cls, request, user) -> None:

        """ The link carries no authentication: it names the person it
            was sent to, so the person is the actor. """

        emit(
            EventName.ACCOUNT_VERIFY,
            account_id=user.account_id,
            actor=Actor.from_user(user),
            event_object=EventObject(
                type=EventObjectType.ACCOUNT, id=user.account_id,
            ),
            request=request,
        )

    @classmethod
    def verification_resent(cls, request, account_owner) -> None:
        cls._request_event(
            EventName.ACCOUNT_VERIFICATION_RESEND,
            request=request,
            object_type=EventObjectType.ACCOUNT,
            object_id=account_owner.account_id,
            payload={'target_email': account_owner.email},
        )

    @classmethod
    def tenant_created(cls, request, tenant) -> None:
        cls._tenant_event(
            EventName.TENANT_CREATE,
            request=request,
            tenant=tenant,
        )

    @classmethod
    def tenant_deleted(cls, request, tenant) -> None:
        cls._tenant_event(
            EventName.TENANT_DELETE,
            request=request,
            tenant=tenant,
        )

    @classmethod
    def purchase_made(
        cls,
        request,
        products: List[Dict[str, Any]],
        checkout_required: bool,
    ) -> None:

        """ checkout_required: no card on file, the user got a link to
            the payment page and the subscription is not paid yet. The
            link itself stays out, it opens that page for anybody.

            The products are a mapping of the price code to the
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
        cls._request_event(
            EventName.BILLING_PURCHASE,
            request=request,
            object_type=EventObjectType.ACCOUNT,
            object_id=request.user.account_id,
            payload={
                'products': quantity_by_code,
                'checkout_required': checkout_required,
            },
        )

    @classmethod
    def subscription_cancelled(cls, request) -> None:
        cls._request_event(
            EventName.BILLING_SUBSCRIPTION_CANCEL,
            request=request,
            object_type=EventObjectType.ACCOUNT,
            object_id=request.user.account_id,
        )

    @classmethod
    def payment_confirmed(
        cls,
        request,
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
        emit(
            EventName.BILLING_PAYMENT_CONFIRM,
            account_id=user.account_id,
            actor=Actor.from_user(user, auth_type),
            event_object=EventObject(
                type=EventObjectType.ACCOUNT, id=user.account_id,
            ),
            payload=payload,
            request=request,
        )

    @classmethod
    def template_saved(
        cls,
        request,
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
            EventName.TEMPLATE_PUBLISH if template.is_active
            else EventName.TEMPLATE_DRAFT_SAVE,
            request=request,
            template=template,
            name=name,
            extra={'source': source} if source else None,
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

        cls._request_event(
            EventName.TEMPLATE_EXPORT,
            request=request,
            object_type=EventObjectType.TEMPLATE,
            payload={'filters': filters},
        )

    @classmethod
    def template_draft_discarded(
        cls,
        request,
        template,
        template_deleted: bool,
    ) -> None:

        """ A template that was never published has nothing to go back
            to: discarding its draft deletes the template itself. """

        cls._template_event(
            EventName.TEMPLATE_DRAFT_DISCARD,
            request=request,
            template=template,
            name=template.name,
            extra={'template_deleted': template_deleted},
        )

    @classmethod
    def template_generated_with_ai(cls, request) -> None:

        """ No payload: the description is text the user typed, and the
            generated template is not saved until the user saves it. """

        cls._request_event(
            EventName.TEMPLATE_AI_GENERATE,
            request=request,
            object_type=EventObjectType.TEMPLATE,
        )

    @classmethod
    def template_filled_from_library(cls, request, system_template) -> None:
        cls._request_event(
            EventName.TEMPLATE_LIBRARY_FILL,
            request=request,
            object_type=EventObjectType.SYSTEM_TEMPLATE,
            object_id=system_template.id,
            payload={'name': system_template.name},
        )

    @classmethod
    def library_templates_imported(
        cls,
        request,
        templates_count: int,
    ) -> None:
        cls._request_event(
            EventName.TEMPLATE_LIBRARY_IMPORT,
            request=request,
            object_type=EventObjectType.SYSTEM_TEMPLATE,
            payload={'templates_count': templates_count},
        )

    @classmethod
    def template_preset_created(cls, request, preset) -> None:
        cls._template_preset_event(
            EventName.TEMPLATE_PRESET_CREATE,
            request=request,
            preset=preset,
        )

    @classmethod
    def template_preset_updated(cls, request, preset) -> None:
        cls._template_preset_event(
            EventName.TEMPLATE_PRESET_UPDATE,
            request=request,
            preset=preset,
        )

    @classmethod
    def template_preset_deleted(cls, request, preset) -> None:
        cls._template_preset_event(
            EventName.TEMPLATE_PRESET_DELETE,
            request=request,
            preset=preset,
        )

    @classmethod
    def template_preset_set_default(cls, request, preset) -> None:
        cls._template_preset_event(
            EventName.TEMPLATE_PRESET_SET_DEFAULT,
            request=request,
            preset=preset,
        )

    @classmethod
    def fieldset_created(cls, request, fieldset) -> None:
        cls._fieldset_event(
            EventName.FIELDSET_CREATE,
            request=request,
            fieldset_id=fieldset.id,
            name=fieldset.name,
        )

    @classmethod
    def fieldset_updated(cls, request, fieldset) -> None:
        cls._fieldset_event(
            EventName.FIELDSET_UPDATE,
            request=request,
            fieldset_id=fieldset.id,
            name=fieldset.name,
        )

    @classmethod
    def fieldset_cloned(cls, request, clone, source_fieldset_id: int) -> None:
        cls._fieldset_event(
            EventName.FIELDSET_CLONE,
            request=request,
            fieldset_id=clone.id,
            name=clone.name,
            extra={'source_fieldset_id': source_fieldset_id},
        )

    @classmethod
    def fieldset_deleted(cls, request, fieldset) -> None:
        cls._fieldset_event(
            EventName.FIELDSET_DELETE,
            request=request,
            fieldset_id=fieldset.id,
            name=fieldset.name,
        )

    @classmethod
    def dataset_created(cls, request, dataset, items_count: int) -> None:
        cls._dataset_event(
            EventName.DATASET_CREATE,
            request=request,
            dataset_id=dataset.id,
            name=dataset.name,
            extra={'items_count': items_count},
        )

    @classmethod
    def dataset_updated(
        cls,
        request,
        dataset,
        changed_fields: List[str],
    ) -> None:
        cls._dataset_event(
            EventName.DATASET_UPDATE,
            request=request,
            dataset_id=dataset.id,
            name=dataset.name,
            extra={'changed_fields': changed_fields},
        )

    @classmethod
    def dataset_deleted(cls, request, dataset) -> None:
        cls._dataset_event(
            EventName.DATASET_DELETE,
            request=request,
            dataset_id=dataset.id,
            name=dataset.name,
        )

    @classmethod
    def dataset_items_added(
        cls,
        request,
        dataset,
        items_count: int,
    ) -> None:
        cls._dataset_event(
            EventName.DATASET_ITEMS_ADD,
            request=request,
            dataset_id=dataset.id,
            name=dataset.name,
            extra={'items_count': items_count},
        )

    @classmethod
    def dataset_items_replaced(
        cls,
        request,
        dataset,
        items_count: int,
    ) -> None:
        cls._dataset_event(
            EventName.DATASET_ITEMS_REPLACE,
            request=request,
            dataset_id=dataset.id,
            name=dataset.name,
            extra={'items_count': items_count},
        )

    @classmethod
    def dataset_item_created(cls, request, item) -> None:
        cls._dataset_item_event(
            EventName.DATASET_ITEM_CREATE,
            request=request,
            item_id=item.id,
            dataset_id=item.dataset_id,
        )

    @classmethod
    def dataset_item_updated(
        cls,
        request,
        item,
        changed_fields: List[str],
    ) -> None:
        cls._dataset_item_event(
            EventName.DATASET_ITEM_UPDATE,
            request=request,
            item_id=item.id,
            dataset_id=item.dataset_id,
            extra={'changed_fields': changed_fields},
        )

    @classmethod
    def dataset_item_deleted(cls, request, item) -> None:
        cls._dataset_item_event(
            EventName.DATASET_ITEM_DELETE,
            request=request,
            item_id=item.id,
            dataset_id=item.dataset_id,
        )

    @classmethod
    def workflow_updated(
        cls,
        request,
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
        cls._request_event(
            EventName.WORKFLOW_UPDATE,
            request=request,
            object_type=EventObjectType.WORKFLOW,
            object_id=workflow.id,
            payload=payload,
            workflow_id=workflow.id,
        )

    @classmethod
    def comment_updated(cls, request, comment) -> None:
        cls._comment_event(
            EventName.TASK_COMMENT_UPDATE,
            request=request,
            comment=comment,
        )

    @classmethod
    def comment_deleted(cls, request, comment) -> None:
        cls._comment_event(
            EventName.TASK_COMMENT_DELETE,
            request=request,
            comment=comment,
        )

    @classmethod
    def checklist_item_marked(
        cls,
        request,
        checklist,
        selection_id: int,
    ) -> None:
        cls._checklist_event(
            EventName.TASK_CHECKLIST_MARK,
            request=request,
            checklist=checklist,
            selection_id=selection_id,
        )

    @classmethod
    def checklist_item_unmarked(
        cls,
        request,
        checklist,
        selection_id: int,
    ) -> None:
        cls._checklist_event(
            EventName.TASK_CHECKLIST_UNMARK,
            request=request,
            checklist=checklist,
            selection_id=selection_id,
        )
