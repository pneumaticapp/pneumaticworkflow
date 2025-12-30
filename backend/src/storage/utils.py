import re
from typing import List

from django.contrib.auth import get_user_model
from django.db import models

from src.processes.models.templates.template import Template
from src.processes.models.workflows.task import Task
from src.processes.models.workflows.workflow import Workflow
from src.storage.enums import SourceType
from src.storage.models import Attachment
from src.storage.services.attachments import AttachmentService

UserModel = get_user_model()


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


def refresh_attachments(
    source: models.Model,
    user: UserModel,
) -> List[str]:
    """
    Updates attachments for source.
    Creates new attachments for found file_id.
    Deletes unused attachments.
    Returns list of new file_id.
    """
    # Determine source type and extract file_ids
    if isinstance(source, Task):
        file_ids = extract_file_ids_from_text(source.description)
        source_type = SourceType.TASK
        filter_kwargs = {'task': source}
    elif isinstance(source, Workflow):
        file_ids = extract_file_ids_from_text(source.description)
        source_type = SourceType.WORKFLOW
        filter_kwargs = {'workflow': source}
    elif isinstance(source, Template):
        file_ids = extract_file_ids_from_text(source.description)
        source_type = SourceType.TEMPLATE
        filter_kwargs = {'template': source}
    else:
        return []

    if not file_ids:
        # Delete all attachments if file_ids not found
        Attachment.objects.filter(
            account_id=source.account_id,
            source_type=source_type,
            **filter_kwargs,
        ).delete()
        return []

    # Get existing attachments
    existent_file_ids = list(
        Attachment.objects
        .filter(
            account_id=source.account_id,
            file_id__in=file_ids,
            source_type=source_type,
            **filter_kwargs,
        )
        .values_list('file_id', flat=True),
    )

    # Delete unused attachments
    Attachment.objects.filter(
        account_id=source.account_id,
        source_type=source_type,
        **filter_kwargs,
    ).exclude(file_id__in=file_ids).delete()

    # Determine new file_ids
    new_files_ids = list(set(file_ids) - set(existent_file_ids))

    # Create new attachments
    if new_files_ids:
        service = AttachmentService(user=user)
        service.bulk_create(file_ids=new_files_ids, source=source)

    return new_files_ids


def get_attachment_description_fields(source: models.Model) -> List[str]:
    """
    Returns list of description fields for source.
    Used to search for file_ids in various fields.
    """
    if isinstance(source, (Task, Workflow, Template)):
        return ['description']

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
