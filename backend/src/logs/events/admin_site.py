"""Audit Django admin hooks with cleaned form data and readable relations."""

from typing import Any, Dict, Iterable, List, Optional, Union

from django.contrib.admin.models import LogEntry
from django.core.files import File
from django.db.models import Model, QuerySet
from django.forms import BaseForm
from django.http import HttpRequest
from django.utils.functional import SimpleLazyObject

from src.logs.events.services import AuditEventService

PASSWORD_FIELDS = ('password', 'password1', 'password2')
NEW_PASSWORD_FIELD = 'password1'
FORM_ATTR = '_journal_form'
ADMIN_ACCOUNT_MODEL = 'accounts.account'
ADMIN_INVITE_MODEL = 'accounts.userinvite'
ChangeMessage = Union[str, List[Dict[str, Any]]]


class JournaledAdminMixin:
    """Keep the admin history and publish the same action to the journal.

    request.user: accounts.User
    """

    def get_journal_target(
        self,
        request: HttpRequest,
        instance: Model,
    ) -> Dict[str, Any]:
        """Model, object and account of the row for the journal.

        An invite id is its acceptance key, so it is never written.
        A row without an account belongs to the account of the admin.
        """
        model = instance._meta.label_lower
        target = {
            'model': model,
            'object_id': instance.pk,
        }
        if model == ADMIN_INVITE_MODEL:
            target['object_id'] = None
        if model == ADMIN_ACCOUNT_MODEL:
            target['account_id'] = instance.pk
            target['account_name'] = instance.name
        elif getattr(instance, 'account_id', None) is not None:
            target['account_id'] = instance.account_id
            target['account_name'] = lambda: instance.account.name
        else:
            target['account_id'] = request.user.account_id
            target['account_name'] = lambda: request.user.account.name
        return target

    def construct_change_message(
        self,
        request: HttpRequest,
        form: BaseForm,
        formsets: Optional[Iterable[Any]],
        add: bool = False,
    ) -> ChangeMessage:
        setattr(request, FORM_ATTR, (form, formsets))
        return super().construct_change_message(
            request=request,
            form=form,
            formsets=formsets,
            add=add,
        )

    def log_addition(
        self,
        request: HttpRequest,
        instance: Model,
        message: ChangeMessage,
    ) -> LogEntry:
        entry = super().log_addition(
            request=request,
            object=instance,
            message=message,
        )
        form, formsets = getattr(request, FORM_ATTR, None) or (None, None)
        setattr(request, FORM_ATTR, None)
        AuditEventService.admin_created(
            user=request.user,
            target=instance,
            form_data=SimpleLazyObject(
                lambda: _form_data(form=form, formsets=formsets),
            ),
            **self.get_journal_target(request=request, instance=instance),
        )
        return entry

    def log_change(
        self,
        request: HttpRequest,
        instance: Model,
        message: ChangeMessage,
    ) -> LogEntry:
        entry = super().log_change(
            request=request,
            object=instance,
            message=message,
        )
        form, formsets = getattr(request, FORM_ATTR, None) or (None, None)
        setattr(request, FORM_ATTR, None)
        is_password_set = (
            form is not None and NEW_PASSWORD_FIELD in form.cleaned_data
        )
        AuditEventService.admin_updated(
            user=request.user,
            target=instance,
            form_data=SimpleLazyObject(
                lambda: _form_data(form=form, formsets=formsets),
            ),
            is_password_set=is_password_set,
            **self.get_journal_target(request=request, instance=instance),
        )
        return entry

    def log_deletion(
        self,
        request: HttpRequest,
        instance: Model,
        object_repr: str,
    ) -> LogEntry:
        entry = super().log_deletion(
            request=request,
            object=instance,
            object_repr=object_repr,
        )
        AuditEventService.admin_deleted(
            user=request.user,
            target=instance,
            **self.get_journal_target(request=request, instance=instance),
        )
        return entry


def _form_data(
    form: Optional[BaseForm],
    formsets: Optional[Iterable[Any]],
) -> Optional[Dict[str, Any]]:
    """Collect submitted rows, excluding passwords and naming relations."""
    if form is None:
        return None
    rows = [(None, form)]
    for formset in formsets or ():
        rows.extend(
            (formset.model._meta.label_lower, inline_form)
            for inline_form in formset.forms
            if inline_form.has_changed()
        )
    form_data = {}
    inlines = {}
    for model, row_form in rows:
        cleaned = {}
        for name, form_value in row_form.cleaned_data.items():
            if name in PASSWORD_FIELDS:
                continue
            value = form_value
            if isinstance(value, QuerySet):
                value = [{'id': item.pk, 'name': str(item)} for item in value]
            elif isinstance(value, Model):
                value = {'id': value.pk, 'name': str(value)}
            elif isinstance(value, File):
                value = value.name
            cleaned[name] = value
        if model is None:
            form_data['data'] = cleaned
        else:
            inlines.setdefault(model, []).append(cleaned)
    if inlines:
        form_data['inlines'] = inlines
    return form_data
