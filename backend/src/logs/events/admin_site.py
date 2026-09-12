""" Audit events of the Django admin site.

    A superuser changes users, accounts and groups there directly, past
    every service that publishes an event. The admin site writes a
    LogEntry for each addition, change and deletion it makes, whatever
    the model and whether a ModelAdmin saves it itself or through a
    bulk action, so one receiver of that row covers all of them. """

import json
from typing import Any, Dict, Iterable, List, Optional, Union

from django.contrib.admin.models import (
    ADDITION,
    CHANGE,
    DELETION,
    LogEntry,
)
from django.core.exceptions import ObjectDoesNotExist

from src.logs.events.emitter import emit
from src.logs.events.enums import EventName, EventObjectType
from src.logs.events.schema import Actor, EventObject

EVENT_TYPES: Dict[int, str] = {
    ADDITION: EventName.ADMIN_CREATE,
    CHANGE: EventName.ADMIN_UPDATE,
    DELETION: EventName.ADMIN_DELETE,
}
OBJECT_TYPES: Dict[str, str] = {
    'accounts.account': EventObjectType.ACCOUNT,
    'accounts.user': EventObjectType.USER,
    'accounts.usergroup': EventObjectType.GROUP,
    'accounts.apikey': EventObjectType.API_KEY,
    'accounts.userinvite': EventObjectType.INVITE,
}
ACCOUNT_MODEL = 'accounts.account'
# The password form of the user admin names its two inputs, not the
# field they set.
PASSWORD_FIELDS: Dict[str, str] = {
    'password1': 'password',
    'password2': 'password',
}


def publish_log_entry(
    sender: Any,
    instance: LogEntry,
    created: bool,
    **kwargs,
) -> None:

    """ post_save receiver of LogEntry, connected in LogsConfig.ready.

        The admin site writes the row inside the request that made the
        change, so emit() finds the address and the browser of the
        superuser in the context of that request. """

    event_type = EVENT_TYPES.get(instance.action_flag)
    if not created or event_type is None:
        return
    label = _model_label(instance)
    payload: Dict[str, Any] = {'model': label}
    payload.update(
        _changes(_parse_change_message(instance.change_message)),
    )
    emit(
        event_type,
        account_id=_account_id(instance, label),
        actor=Actor.from_user(instance.user),
        event_object=EventObject(
            type=OBJECT_TYPES.get(label, EventObjectType.OTHER),
            id=_object_id(instance.object_id),
        ),
        payload=payload,
    )


def _model_label(entry: LogEntry) -> str:
    if entry.content_type_id is None:
        return ''
    return f'{entry.content_type.app_label}.{entry.content_type.model}'


def _object_id(value: Optional[str]) -> Optional[Union[int, str]]:
    if value is None:
        return None
    return int(value) if value.isdigit() else value


def _account_id(entry: LogEntry, label: str) -> int:

    """ The account the changed row belongs to, so that the account
        sees what a superuser did to it. A row of no account, a product
        or a system message, goes to the account of the superuser.

        A deleted row is still in the table here: the admin site logs
        a deletion before it deletes. A row logged by anything else
        after a delete falls back to the account of whoever wrote the
        log. """

    object_id = _object_id(entry.object_id)
    if label == ACCOUNT_MODEL and isinstance(object_id, int):
        return object_id
    try:
        edited = entry.get_edited_object()
    except (ObjectDoesNotExist, AttributeError, ValueError):
        edited = None
    account_id = getattr(edited, 'account_id', None)
    if account_id is None:
        return entry.user.account_id
    return account_id


def _changes(messages: Optional[list]) -> Dict[str, Any]:

    """ Names of the changed fields and the inline rows touched.

        The message the admin site stores also holds the text form of
        each inline row, and that is the e-mail of a user as often as
        not: only the model and the field names are kept.

        An inline change is one line, "changed Group: name, photo", and
        not an object: normalize_payload turns an object inside a list
        into one JSON string anyway. """

    if not isinstance(messages, list):
        return {}
    fields: List[str] = []
    inlines: List[str] = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        for action, value in message.items():
            details = value if isinstance(value, dict) else {}
            names = _field_names(details.get('fields') or ())
            if 'name' in details:
                inlines.append(_inline_change(action, details['name'], names))
            else:
                fields.extend(names)
    changes: Dict[str, Any] = {}
    if fields:
        changes['changed_fields'] = sorted(set(fields))
    if inlines:
        changes['inline_changes'] = inlines
    return changes


def _inline_change(action: str, model: Any, fields: List[str]) -> str:
    change = f'{action} {model}'
    if fields:
        change = f'{change}: {", ".join(fields)}'
    return change


def _field_names(fields: Iterable[Any]) -> List[str]:
    return sorted({
        PASSWORD_FIELDS.get(str(name), str(name)) for name in fields
    })


def _parse_change_message(value: str) -> Any:

    """ The JSON the admin site stores in LogEntry.change_message. A
        row written by hand may hold plain text instead: it says
        nothing about fields, so it is read as no changes. """

    try:
        return json.loads(value or '[]')
    except ValueError:
        return None
