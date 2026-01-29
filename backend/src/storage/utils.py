import re
from typing import List, Optional

from django.contrib.auth import get_user_model
from django.db import models

from src.storage.enums import AccessType, SourceType
from src.processes.models.templates.template import Template
from src.processes.models.workflows.event import WorkflowEvent
from src.processes.models.workflows.task import Task
from src.processes.models.workflows.workflow import Workflow
from src.storage.models import Attachment
from src.storage.services.attachments import AttachmentService

UserModel = get_user_model()


def check_attachments(
    source: models.Model,
    user: UserModel,
) -> List[str]:
    """
    Finds and updates attachments for source.
    Alias for refresh_attachments for backward compatibility.
    """
    return refresh_attachments(source=source, user=user)


def extract_file_ids_from_text(text: str) -> List[str]:
    """
    Extracts file_id from text.
    Searches for file service links in formats:
    - http(s)://domain/files/{file_id}
    - http(s)://domain/api/files/{file_id}
    """
    if not text:
        return []

    # Pattern for searching file service links
    # Supports various URL formats
    patterns = [
        r'/files/([a-zA-Z0-9_-]{8,64})',
        r'/api/files/([a-zA-Z0-9_-]{8,64})',
        r'file_id[=:]([a-zA-Z0-9_-]{8,64})',
    ]

    file_ids = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        file_ids.extend(matches)

    # Remove duplicates
    return list(set(file_ids))


def extract_file_ids_from_values(
    values: List[Optional[str]],
) -> List[str]:
    file_ids = []
    for value in values:
        if value:
            file_ids.extend(extract_file_ids_from_text(value))
    return list(set(file_ids))


def sync_storage_attachments_for_scope(
    account,
    user: Optional[UserModel],
    add_file_ids: List[str],
    remove_file_ids: List[str],
    source_type: str,
    task=None,
    workflow=None,
    template=None,
    access_type: str = AccessType.RESTRICTED,
):
    filter_kwargs = {
        'account_id': account.id,
        'source_type': source_type,
        'task': task,
        'workflow': workflow,
        'template': template,
    }
    if remove_file_ids:
        Attachment.objects.filter(
            file_id__in=remove_file_ids,
            **filter_kwargs,
        ).delete()
    if add_file_ids:
        service = AttachmentService(user=user)
        service.bulk_create_for_scope(
            file_ids=add_file_ids,
            account=account,
            source_type=source_type,
            access_type=access_type,
            task=task,
            workflow=workflow,
            template=template,
        )


def sync_account_file_fields(
    account,
    user: Optional[UserModel],
    old_values: List[Optional[str]],
    new_values: List[Optional[str]],
):
    old_file_ids = extract_file_ids_from_values(old_values)
    new_file_ids = extract_file_ids_from_values(new_values)
    removed_file_ids = list(set(old_file_ids) - set(new_file_ids))
    added_file_ids = list(set(new_file_ids) - set(old_file_ids))
    sync_storage_attachments_for_scope(
        account=account,
        user=user,
        add_file_ids=added_file_ids,
        remove_file_ids=removed_file_ids,
        source_type=SourceType.ACCOUNT,
        access_type=AccessType.ACCOUNT,
    )


def refresh_attachments_for_text(
    account,
    user: UserModel,
    text: Optional[str],
    source_type: str,
    task=None,
    workflow=None,
    template=None,
) -> List[str]:
    file_ids = extract_file_ids_from_text(text)
    filter_kwargs = {
        'account_id': account.id,
        'source_type': source_type,
        'task': task,
        'workflow': workflow,
        'template': template,
    }
    if not file_ids:
        Attachment.objects.filter(**filter_kwargs).delete()
        return []
    existent_file_ids = list(
        Attachment.objects.filter(
            file_id__in=file_ids,
            **filter_kwargs,
        ).values_list('file_id', flat=True),
    )
    Attachment.objects.filter(
        **filter_kwargs,
    ).exclude(file_id__in=file_ids).delete()
    new_files_ids = list(set(file_ids) - set(existent_file_ids))
    if new_files_ids:
        service = AttachmentService(user=user)
        service.bulk_create_for_scope(
            file_ids=new_files_ids,
            account=account,
            source_type=source_type,
            task=task,
            workflow=workflow,
            template=template,
        )
    return new_files_ids


def refresh_attachments(
    source: models.Model,
    user: UserModel,
) -> List[str]:
    """
    Updates attachments for source.
    Creates new attachments for found file_id.
    Deletes unused attachments.
    Returns list of new file_id.

    Supports:
    - Task: extracts from description field
    - Workflow: extracts from description field
    - Template: extracts from description field
    - WorkflowEvent (comment): extracts from text field
    """
    # Determine source type and extract file_ids
    if isinstance(source, Task):
        return refresh_attachments_for_text(
            account=source.account,
            user=user,
            text=source.description,
            source_type=SourceType.TASK,
            task=source,
        )
    if isinstance(source, Workflow):
        return refresh_attachments_for_text(
            account=source.account,
            user=user,
            text=source.description,
            source_type=SourceType.WORKFLOW,
            workflow=source,
        )
    if isinstance(source, Template):
        return refresh_attachments_for_text(
            account=source.account,
            user=user,
            text=source.description,
            source_type=SourceType.TEMPLATE,
            template=source,
        )
    if isinstance(source, WorkflowEvent):
        # For comments, use task if available, otherwise workflow
        # SourceType is TASK if task exists, WORKFLOW otherwise
        source_type = (
            SourceType.TASK
            if source.task_id
            else SourceType.WORKFLOW
        )
        new_file_ids = refresh_attachments_for_text(
            account=source.account,
            user=user,
            text=source.text,
            source_type=source_type,
            task=source.task,
            workflow=source.workflow,
        )
        # Update with_attachments field for WorkflowEvent
        has_attachments = bool(extract_file_ids_from_text(source.text))
        if source.with_attachments != has_attachments:
            source.with_attachments = has_attachments
            source.save(update_fields=['with_attachments'])
        return new_file_ids
    return []


def get_attachment_description_fields(source: models.Model) -> List[str]:
    """
    Returns list of description fields for source.
    Used to search for file_ids in various fields.
    """
    if isinstance(source, (Task, Workflow, Template)):
        return ['description']
    if isinstance(source, WorkflowEvent):
        return ['text']

    return []


def extract_all_file_ids_from_source(
    source: models.Model,
) -> List[str]:
    """
    Extracts all file_ids from all text fields of source.
    """
    fields = get_attachment_description_fields(source)
    all_file_ids = []

    for field_name in fields:
        text = getattr(source, field_name, None)
        if text:
            file_ids = extract_file_ids_from_text(text)
            all_file_ids.extend(file_ids)

    return list(set(all_file_ids))
