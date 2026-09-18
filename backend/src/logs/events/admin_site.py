""" Audit events of the Django admin site.

    A superuser changes users, accounts and groups there directly, past
    every service that publishes an event. The admin site reports each
    addition, change and deletion it makes to the log_* hooks of the
    ModelAdmin - the change form, the password form, the inlines and
    the "delete selected" action all go through them - so the hooks
    are where the journal is written from. JournaledAdminMixin adds
    that to the ModelAdmin of a model worth journaling. """

from typing import Any, Dict, Iterable, List

from src.logs.events.services import AuditEventService

# The password form of the user admin names its two inputs, not the
# field they set.
PASSWORD_FIELDS: Dict[str, str] = {
    'password1': 'password',
    'password2': 'password',
}


class JournaledAdminMixin:

    """ Publish an audit event for every row the admin site writes.

        The three hooks keep writing the LogEntry the admin site shows
        in its history, then publish the same fact to the journal. The
        deletion hook runs before the delete, so the row and its
        account are still there. """

    # The hooks are called positionally by the admin site, so the
    # second argument is named after what it is, not "object".

    def log_addition(self, request, instance, message):
        entry = super().log_addition(request, instance, message)
        AuditEventService.admin_created(
            user=request.user,
            target=instance,
            model=_model_label(instance),
            changes=_changes(message),
        )
        return entry

    def log_change(self, request, instance, message):
        entry = super().log_change(request, instance, message)
        AuditEventService.admin_updated(
            user=request.user,
            target=instance,
            model=_model_label(instance),
            changes=_changes(message),
        )
        return entry

    def log_deletion(self, request, instance, object_repr):
        entry = super().log_deletion(request, instance, object_repr)
        AuditEventService.admin_deleted(
            user=request.user,
            target=instance,
            model=_model_label(instance),
        )
        return entry


def _model_label(instance: Any) -> str:
    opts = instance._meta
    return f'{opts.app_label}.{opts.model_name}'


def _changes(messages: Any) -> Dict[str, Any]:

    """ Names of the changed fields and the inline rows touched, from
        the message the admin site builds for its own log
        (construct_change_message).

        The message also holds the text form of each inline row, and
        that is the e-mail of a user as often as not: only the model
        and the field names are kept.

        An inline change is one line, "changed Group: name, photo", and
        not an object: normalize_payload turns an object inside a list
        into one JSON string anyway. A message that is plain text says
        nothing about fields and is read as no changes. """

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
