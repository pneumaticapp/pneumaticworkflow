from contextlib import contextmanager
from django.db import transaction
from django.contrib.auth import get_user_model
from celery import shared_task
from celery.task import Task as TaskCelery
from src.accounts.enums import NotificationType
from src.accounts.models import Account, Contact, UserGroup
from src.logs.models import AccountEvent
from src.logs.enums import AccountEventStatus
from src.logs.service import AccountLogService
from src.processes.enums import (
    WorkflowEventType,
    FieldType,
)
from src.processes.models.templates.template import TemplateDraft
from src.processes.models.templates.task import TaskTemplate
from src.processes.models.workflows.task import Task
from src.processes.models.workflows.event import WorkflowEvent
from src.processes.models.workflows.attachment import FileAttachment
from src.processes.models.workflows.fields import TaskField
from src.accounts.models import Notification
from src.storage.google_cloud import GoogleCloudService


# TODO Remove file in https://my.pneumatic.app/workflows/41526
fields_text_types = (
    FieldType.STRING,
    FieldType.TEXT,
    FieldType.URL,
    FieldType.FILE,
)
UserModel = get_user_model()


@contextmanager
def log_operation(user, log_title: str, account_id: int):
    if (
        AccountEvent.objects
        .on_account(account_id)
        .filter(title=log_title)
        .type_system()
        .success()
        .exists()
    ):
        service = AccountLogService(user)
        service.system_log(
            title=log_title,
            status=AccountEventStatus.PENDING,
            user=user,
            data={'status': 'Switching has already been done'},
        )
    try:
        with transaction.atomic():
            yield
    except Exception as ex:
        service = AccountLogService(user)
        service.system_log(
            title=log_title,
            status=AccountEventStatus.FAILED,
            user=user,
            data={'exception': str(ex)},
        )
        raise


def switch_account_logo(
    user,
    account_id: int,
    path_from: str,
    path_to: str,
):
    log_title = 'Switch account logo'
    qst = Account.objects.filter(id=account_id)
    ids = []
    with log_operation(user, log_title, account_id):
        for account in qst:
            processed = False
            if account.logo_lg and account.logo_lg.find(path_from) > -1:
                account.logo_lg = account.logo_lg.replace(
                    path_from,
                    path_to,
                )
                processed = True
            if account.logo_sm and account.logo_sm.find(path_from) > -1:
                account.logo_sm = account.logo_sm.replace(path_from, path_to)
                processed = True
            if processed:
                account.save(update_fields=['logo_sm', 'logo_lg'])
                ids.append(account.id)

    service = AccountLogService(user)
    service.system_log(
        title=log_title,
        status=AccountEventStatus.SUCCESS,
        user=user,
        data={
            'processed': len(ids),
            'ids': ids,
        },
    )


def switch_user_avatars(
    user,
    account_id: int,
    path_from: str,
    path_to: str,
):
    log_title = 'Switch user avatars'
    qst = (
        UserModel.objects
        .on_account(account_id)
        .exclude(photo__isnull=True)
    )
    ids = []
    with log_operation(user, log_title, account_id):
        for u in qst:
            if u.photo.find(path_from) > -1:
                u.photo = u.photo.replace(path_from, path_to)
                u.save(update_fields=['photo'])
                ids.append(u.id)

    service = AccountLogService(user)
    service.system_log(
        title=log_title,
        status=AccountEventStatus.SUCCESS,
        user=user,
        data={'processed': len(ids), 'ids': ids},
    )


def switch_user_contacts(
    user,
    account_id: int,
    path_from: str,
    path_to: str,
):
    log_title = 'Switch user contacts avatars'
    qst = (
        Contact.objects
        .on_account(account_id)
        .exclude(photo__isnull=True)
    )
    ids = []
    with log_operation(user, log_title, account_id):
        for contact in qst:
            if contact.photo.find(path_from) > -1:
                contact.photo = contact.photo.replace(path_from, path_to)
                contact.save(update_fields=['photo'])
                ids.append(contact.id)

    service = AccountLogService(user)
    service.system_log(
        title=log_title,
        status=AccountEventStatus.SUCCESS,
        user=user,
        data={'processed': len(ids), 'ids': ids},
    )


def switch_groups(
    user,
    account_id: int,
    path_from: str,
    path_to: str,
):
    log_title = 'Switch groups photos'
    qst = (
        UserGroup.objects
        .on_account(account_id)
        .exclude(photo__isnull=True)
    )
    ids = []
    with log_operation(user, log_title, account_id):
        for group in qst:
            if group.photo.find(path_from) > -1:
                group.photo = group.photo.replace(path_from, path_to)
                group.save(update_fields=['photo'])
                ids.append(group.id)

    service = AccountLogService(user)
    service.system_log(
        title=log_title,
        status=AccountEventStatus.SUCCESS,
        user=user,
        data={'processed': len(ids), 'ids': ids},
    )


def switch_attachments(
    user,
    account_id: int,
    path_from: str,
    path_to: str,
):
    # Migrate FileAttachments
    log_title = 'Switch attachments'
    qst = (
        FileAttachment.objects
        .on_account(account_id)
        .only('url')
    )
    ids = []
    with log_operation(user, log_title, account_id):
        for file in qst:
            processed = False
            if file.url.find(path_from) > -1:
                file.url = file.url.replace(path_from, path_to)
                processed = True
            if file.thumbnail_url and file.thumbnail_url.find(path_from) > -1:
                file.thumbnail_url = file.thumbnail_url.replace(
                    path_from,
                    path_to,
                )
                processed = True
            if processed:
                file.save(update_fields=['url', 'thumbnail_url'])
                ids.append(file.id)

    service = AccountLogService(user)
    service.system_log(
        title=log_title,
        status=AccountEventStatus.SUCCESS,
        user=user,
        data={'processed': len(ids), 'ids': ids},
    )


def switch_task_templates(
    user,
    account_id: int,
    path_from: str,
    path_to: str,
):
    # TemplateTask description
    log_title = 'Switch template tasks'
    qst = (
        TaskTemplate.objects
        .on_account(account_id)
        .all()
    )
    ids = []
    with log_operation(user, log_title, account_id):
        for task_template in qst:
            if task_template.description.find(path_from) > -1:
                task_template.description = task_template.description.replace(
                    path_from,
                    path_to,
                )
                task_template.save(update_fields=['description'])
                ids.append(task_template.id)

    service = AccountLogService(user)
    service.system_log(
        title=log_title,
        status=AccountEventStatus.SUCCESS,
        user=user,
        data={'processed': len(ids), 'ids': ids},
    )


def switch_tasks(
    user,
    account_id: int,
    path_from: str,
    path_to: str,
):
    # Task description
    log_title = 'Switch tasks'
    qst = (
        Task.objects
        .on_account(account_id)
    )
    ids = []
    with log_operation(user, log_title, account_id):
        for task in qst:
            if task.description.find(path_from) > -1:
                task.description = task.description.replace(path_from, path_to)
                task.save(update_fields=['description'])
                ids.append(task.id)

    service = AccountLogService(user)
    service.system_log(
        title=log_title,
        status=AccountEventStatus.SUCCESS,
        user=user,
        data={'processed': len(ids), 'ids': ids},
    )


def switch_comments(
    user,
    account_id: int,
    path_from: str,
    path_to: str,
):
    # WorkflowEvent type comment text
    log_title = 'Switch comments'
    qst = (
        WorkflowEvent.objects
        .on_account(account_id)
        .type_comment()
        .exclude(text__isnull=True)
    )
    ids = []
    with log_operation(user, log_title, account_id):
        for event in qst:
            if event.text.find(path_from) > -1:
                event.text = event.text.replace(path_from, path_to)
                event.clear_text = event.clear_text.replace(path_from, path_to)
                event.save(update_fields=['text', 'clear_text'])
                ids.append(event.id)

    service = AccountLogService(user)
    service.system_log(
        title=log_title,
        status=AccountEventStatus.SUCCESS,
        user=user,
        data={'processed': len(ids), 'ids': ids},
    )


def switch_revert_events(
    user,
    account_id: int,
    path_from: str,
    path_to: str,
):
    # WorkflowEvent type revert text
    log_title = 'Switch revert events'
    qst = (
        WorkflowEvent.objects
        .on_account(account_id)
        .filter(type=WorkflowEventType.TASK_REVERT)
        .exclude(text__isnull=True)
    )
    ids = []
    with log_operation(user, log_title, account_id):
        for event in qst:
            if event.text.find(path_from) > -1:
                event.text = event.text.replace(path_from, path_to)
                event.clear_text = event.clear_text.replace(path_from, path_to)
                event.save(update_fields=['text', 'clear_text'])
                ids.append(event.id)

    service = AccountLogService(user)
    service.system_log(
        title=log_title,
        status=AccountEventStatus.SUCCESS,
        user=user,
        data={'processed': len(ids), 'ids': ids},
    )


def switch_complete_task_events(
    user,
    account_id: int,
    path_from: str,
    path_to: str,
):
    # WorkflowEvent type complete task task_json fields
    log_title = 'Switch complete task events'
    qst = (
        WorkflowEvent.objects
        .on_account(account_id)
        .filter(type=WorkflowEventType.TASK_COMPLETE)
    )
    ids = []
    with log_operation(user, log_title, account_id):
        for event in qst:
            processed = False
            task = event.task_json
            if not task:
                continue
            if (
                task['description']
                and task['description'].find(path_from) > -1
            ):
                task['description'] = task['description'].replace(
                    path_from,
                    path_to,
                )
                processed = True
            for field in (task.get('output') or []):
                if field['type'] in fields_text_types:
                    if (
                        field.get('value')
                        and field['value'].find(path_from) > -1
                    ):
                        field['value'] = (
                            field['value'].replace(path_from, path_to)
                        )
                        processed = True
                    if (
                        field.get('markdown_value')
                        and field['markdown_value'].find(path_from) > -1
                    ):
                        field['markdown_value'] = (
                            field['markdown_value'].replace(path_from, path_to)
                        )
                        processed = True
                    if (
                        field.get('clear_value')
                        and field['clear_value'].find(path_from) > -1
                    ):
                        field['clear_value'] = (
                            field['clear_value'].replace(path_from, path_to)
                        )
                        processed = True

                if field['type'] == FieldType.FILE:
                    for attach in (field.get('attachments') or []):
                        if attach['url'].find(path_from) > -1:
                            attach['url'] = (
                                attach['url'].replace(path_from, path_to)
                            )
                            if attach['thumbnail_url']:
                                attach['thumbnail_url'] = (
                                    attach['thumbnail_url'].replace(
                                        path_from,
                                        path_to,
                                    )
                                )
                            processed = True
            if processed:
                event.task_json = task
                event.save(update_fields=['task_json'])
                ids.append(event.id)

    service = AccountLogService(user)
    service.system_log(
        title=log_title,
        status=AccountEventStatus.SUCCESS,
        user=user,
        data={'processed': len(ids), 'ids': ids},
    )


def switch_notifications(
    user,
    account_id: int,
    path_from: str,
    path_to: str,
):
    # Notification text
    log_title = 'Switch notifications'
    qst = (
        Notification.objects
        .on_account(account_id)
        .filter(
            type__in=(
                NotificationType.COMMENT,
                NotificationType.MENTION,
            ),
        )
    )
    ids = []
    with log_operation(user, log_title, account_id):
        for noti in qst:
            if noti.text and noti.text.find(path_from) > -1:
                noti.text = noti.text.replace(path_from, path_to)
                noti.save(update_fields=['text'])
                ids.append(noti.id)

    service = AccountLogService(user)
    service.system_log(
        title=log_title,
        status=AccountEventStatus.SUCCESS,
        user=user,
        data={'processed': len(ids), 'ids': ids},
    )


def switch_fields(
    user,
    account_id: int,
    path_from: str,
    path_to: str,
):
    # TaskField value
    log_title = 'Switch fields'
    qst = (
        TaskField.objects
        .filter(
            type__in=fields_text_types,
            workflow__account_id=account_id,
        )
    )
    ids = []
    with log_operation(user, log_title, account_id):
        for field in qst:
            if field.value and field.value.find(path_from) > -1:
                field.value = field.value.replace(path_from, path_to)
                field.markdown_value = field.markdown_value.replace(
                    path_from,
                    path_to,
                )
                field.clear_value = field.clear_value.replace(
                    path_from,
                    path_to,
                )
                field.save(
                    update_fields=['value', 'markdown_value', 'clear_value'],
                )
                ids.append(field.id)

    service = AccountLogService(user)
    service.system_log(
        title=log_title,
        status=AccountEventStatus.SUCCESS,
        user=user,
        data={'processed': len(ids), 'ids': ids},
    )


def switch_template_drafts(
    user,
    account_id: int,
    path_from: str,
    path_to: str,
):

    log_title = 'Switch draft: template tasks'
    qst = (
        TemplateDraft.objects
        .on_account(account_id)
        .exclude(draft__isnull=True)
    )
    ids = []
    with log_operation(user, log_title, account_id):
        for draft in qst:
            processed = False
            data = draft.draft
            for task in (data.get('tasks') or []):
                if (
                    task.get('description')
                    and task['description'].find(path_from) > -1
                ):
                    task['description'] = task['description'].replace(
                        path_from,
                        path_to,
                    )
                    processed = True
            if processed:
                draft.draft = data
                draft.save()
                ids.append(draft.id)

    service = AccountLogService(user)
    service.system_log(
        title=log_title,
        status=AccountEventStatus.SUCCESS,
        user=user,
        data={'processed': len(ids), 'ids': ids},
    )


@shared_task(base=TaskCelery)
def switch_access_to_files(
    user_id,
    account_id: int,
    public_access: bool = False,
):

    user = UserModel.objects.get(id=user_id)
    account = Account.objects.get(id=account_id)
    cloud_service = GoogleCloudService(account=account)
    if public_access:
        path_from = cloud_service.authenticated_bucket_path
        path_to = cloud_service.public_bucket_path
    else:
        path_from = cloud_service.public_bucket_path
        path_to = cloud_service.authenticated_bucket_path

    switch_account_logo(user, account_id, path_from, path_to)
    switch_user_avatars(user, account_id, path_from, path_to)
    switch_user_contacts(user, account_id, path_from, path_to)
    switch_groups(user, account_id, path_from, path_to)
    switch_attachments(user, account_id, path_from, path_to)
    switch_task_templates(user, account_id, path_from, path_to)
    switch_tasks(user, account_id, path_from, path_to)
    switch_comments(user, account_id, path_from, path_to)
    switch_revert_events(user, account_id, path_from, path_to)
    switch_complete_task_events(user, account_id, path_from, path_to)
    switch_notifications(user, account_id, path_from, path_to)
    switch_fields(user, account_id, path_from, path_to)
    switch_template_drafts(user, account_id, path_from, path_to)
