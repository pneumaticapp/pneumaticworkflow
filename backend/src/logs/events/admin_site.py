""" Audit events of the Django admin site.

    A superuser changes users, accounts and groups there directly, past
    every service that publishes an event. The admin site reports each
    addition, change and deletion it makes to the log_* hooks of the
    ModelAdmin - the change form, the password form, the inlines and
    the "delete selected" action all go through them - so the hooks
    are where the journal is written from. JournaledAdminMixin adds
    that to the ModelAdmin of a model worth journaling.

    save_model and delete_model are not enough: the user admin signs
    up a new account in save_model instead of saving the row, and the
    password form of a user and "delete selected" bypass both. """

from typing import Any, Dict, Iterable, Optional, Tuple

from django.core.files import File
from django.db.models import QuerySet
from django.forms import BaseForm

from src.logs.events.emitter import logs_enabled
from src.logs.events.services import AuditEventService

# The inputs of a password: the two of the creation form and of the
# password form of a user, and the hash the change form shows. None of
# them goes into the journal.
PASSWORD_FIELDS = ('password', 'password1', 'password2')
# The input a new password is typed into.
NEW_PASSWORD_FIELD = 'password1'
# The request attribute that carries the form from
# construct_change_message to the log_* hook the admin site calls next.
FORM_ATTR = '_journal_form'


class JournaledAdminMixin:

    """ Publish an audit event for every row the admin site writes.

        The three hooks keep writing the LogEntry the admin site shows
        in its history, then publish the same fact to the journal with
        the data of the form. The deletion hook runs before the
        delete, so the row and its account are still there. """

    def construct_change_message(self, request, form, formsets, add=False):

        """ Every path of the admin site that writes a row - the change
            form, the rows of the changelist, the password form of a
            user - builds the message of its own log from the form
            right before it calls log_addition or log_change with the
            message alone. The form waits on the request for that
            hook. """

        setattr(request, FORM_ATTR, (form, formsets))
        return super().construct_change_message(
            request,
            form,
            formsets,
            add,
        )

    # The hooks are called positionally by the admin site, so the
    # second argument is named after what it is, not "object".

    def log_addition(self, request, instance, message):
        entry = super().log_addition(request, instance, message)
        form, formsets = _pop_form(request)
        AuditEventService.admin_created(
            user=request.user,
            target=instance,
            model=_model_label(instance),
            form_data=_form_data(form, formsets),
        )
        return entry

    def log_change(self, request, instance, message):
        entry = super().log_change(request, instance, message)
        form, formsets = _pop_form(request)
        AuditEventService.admin_updated(
            user=request.user,
            target=instance,
            model=_model_label(instance),
            form_data=_form_data(form, formsets),
            is_password_set=(
                form is not None
                and NEW_PASSWORD_FIELD in form.cleaned_data
            ),
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


def _pop_form(request) -> Tuple[Optional[BaseForm], Optional[Iterable]]:

    """ The form of this write, once: the rows of the changelist are
        saved one after another on the same request. A hook called
        without a form before it (a custom action) gets none. """

    form, formsets = getattr(request, FORM_ATTR, None) or (None, None)
    setattr(request, FORM_ATTR, None)
    return form, formsets


def _form_data(
    form: Optional[BaseForm],
    formsets: Optional[Iterable[Any]],
) -> Optional[Dict[str, Any]]:

    """ What the superuser submitted, as the form cleaned it: the
        fields of the row and the inline rows the admin site wrote. An
        inline row is saved only when its form has changed - the rest
        of them were not written, and an account has as many of them
        as it has users. A password is left out.

        Nothing is collected with the journal off: the ids of every
        many-to-many field are a query, and the service would drop
        the result unread. """

    if form is None or not logs_enabled():
        return None
    form_data: Dict[str, Any] = {'data': _cleaned_data(form)}
    inlines = {}
    for formset in formsets or ():
        rows = [
            _cleaned_data(inline_form)
            for inline_form in formset.forms
            if inline_form.has_changed()
        ]
        if rows:
            inlines[_model_label(formset.model)] = rows
    if inlines:
        form_data['inlines'] = inlines
    return form_data


def _cleaned_data(form: BaseForm) -> Dict[str, Any]:
    return {
        name: _form_value(value)
        for name, value in form.cleaned_data.items()
        if name not in PASSWORD_FIELDS
    }


def _form_value(value: Any) -> Any:

    """ A value of the form the way a payload holds it: a set of rows
        of a many-to-many field is their ids, an uploaded file its
        name. normalize_payload turns a single row into its id. """

    if isinstance(value, QuerySet):
        return list(value.values_list('pk', flat=True))
    if isinstance(value, File):
        return value.name
    return value
