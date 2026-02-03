import re
from typing import List, Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models, IntegrityError

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


def _get_file_service_url_pattern() -> str:
    """
    Returns file service URL pattern based on settings.

    Returns:
        URL pattern for file service
    """
    # Single file service endpoint pattern
    return r'/files/([a-zA-Z0-9_-]{8,64})'


def extract_file_ids_from_text(text: str) -> List[str]:
    """
    Extracts file_id from text for Pneumatic file service links.

    Searches for file service links in formats:
    - http(s)://files.pneumatic.app/files/{file_id}
    - Markdown links: [filename](url_with_file_id)

    Only extracts file_ids from file service domain (settings.FILE_DOMAIN).
    External links (Google Drive, Dropbox, etc.) are ignored.

    Args:
        text: Text content to search in

    Returns:
        List of unique file_ids from file service
    """
    if not text:
        return []

    file_domain = settings.FILE_DOMAIN
    if not file_domain:
        return []

    url_pattern = _get_file_service_url_pattern()

    file_ids = []

    # Extract from Markdown links: [filename](url)
    markdown_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    markdown_matches = re.findall(markdown_pattern, text)

    for _filename, url in markdown_matches:
        if file_domain in url:
            matches = re.findall(url_pattern, url)
            file_ids.extend(matches)

    # Also check for direct URLs in text (no markdown)
    full_pattern = rf'https?://[^/]*{re.escape(file_domain)}{url_pattern}'
    matches = re.findall(full_pattern, text)
    file_ids.extend(matches)

    # Remove duplicates and return
    return list(set(file_ids))


def extract_all_links_from_text(text: str) -> List[dict]:
    """
    Extracts all file links from text (both file service and external).

    Returns list of dictionaries with link information:
    {
        'filename': 'document.pdf',
        'url': 'https://files.example.com/files/abc123',
        'file_id': 'abc123',  # Only for file service links
        'is_file_service': True/False
    }

    Args:
        text: Text content to search in

    Returns:
        List of link dictionaries
    """
    if not text:
        return []

    file_domain = settings.FILE_DOMAIN
    if not file_domain:
        return []

    url_pattern = _get_file_service_url_pattern()

    links = []

    # Extract from Markdown links: [filename](url)
    markdown_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    markdown_matches = re.findall(markdown_pattern, text)

    for filename, url in markdown_matches:
        link_info = {
            'filename': filename,
            'url': url,
            'file_id': None,
            'is_file_service': False,
        }

        if file_domain in url:
            link_info['is_file_service'] = True
            # Extract file_id using single pattern
            matches = re.findall(url_pattern, url)
            if matches:
                link_info['file_id'] = matches[0]

        links.append(link_info)

    return links


def extract_file_ids_from_values(
    values: List[Optional[str]],
) -> List[str]:
    """
    Extracts file_ids from list of text values.
    Only returns file_ids from file service links.
    """
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


def refresh_attachments_for_event(
    account,
    user: UserModel,
    text: Optional[str],
    event,
) -> List[str]:
    """
    Refreshes attachments for workflow event (comment).

    Args:
        account: Account
        user: User
        text: Text to analyze
        event: Workflow event

    Returns:
        List of new file_ids
    """
    file_ids = extract_file_ids_from_text(text)

    # Determine source_type: TASK if task exists, else WORKFLOW
    source_type = (
        SourceType.TASK
        if event.task_id
        else SourceType.WORKFLOW
    )

    # Build filter_kwargs for event
    filter_kwargs = {
        'account_id': account.id,
        'source_type': source_type,
        'event': event,
    }

    # If no files in text - delete all event attachments
    if not file_ids:
        Attachment.objects.filter(**filter_kwargs).delete()
        return []

    # Get existing file_ids
    existent_file_ids = list(
        Attachment.objects.filter(
            file_id__in=file_ids,
            **filter_kwargs,
        ).values_list('file_id', flat=True),
    )

    # Remove attachments no longer present in text
    Attachment.objects.filter(
        **filter_kwargs,
    ).exclude(file_id__in=file_ids).delete()

    # Create new attachments
    new_files_ids = list(set(file_ids) - set(existent_file_ids))
    if new_files_ids:
        try:
            service = AttachmentService(user=user)
            service.bulk_create_for_event(
                file_ids=new_files_ids,
                account=account,
                source_type=source_type,
                event=event,
            )
        except (ValueError, TypeError, IntegrityError):
            return []

    return new_files_ids


def refresh_attachments_for_text(
    account,
    user: UserModel,
    text: Optional[str],
    source_type: str,
    task=None,
    workflow=None,
    template=None,
) -> List[str]:
    """
    Refreshes attachments for a text field.

    Args:
        account: Account
        user: User
        text: Text to analyze
        source_type: Source type (TASK, WORKFLOW, TEMPLATE)
        task: Task (optional)
        workflow: Workflow (optional)
        template: Template (optional)

    Returns:
        List of new file_ids
    """
    file_ids = extract_file_ids_from_text(text)

    # Build filter_kwargs, excluding None for precise filtering
    filter_kwargs = {
        'account_id': account.id,
        'source_type': source_type,
    }

    # Add only non-None values for correct filtering
    if task is not None:
        filter_kwargs['task'] = task
    if workflow is not None:
        filter_kwargs['workflow'] = workflow
    if template is not None:
        filter_kwargs['template'] = template

    # If no files in text - delete only attachments not linked to fields
    if not file_ids:
        # Do not delete attachments linked to fields (output != None)
        Attachment.objects.filter(
            **filter_kwargs,
            output__isnull=True,  # Delete only those not linked to fields
        ).delete()
        return []

    # Get existing file_ids
    existent_file_ids = list(
        Attachment.objects.filter(
            file_id__in=file_ids,
            **filter_kwargs,
        ).values_list('file_id', flat=True),
    )

    # Remove attachments no longer in text (but not those linked to fields)
    Attachment.objects.filter(
        **filter_kwargs,
        output__isnull=True,  # Delete only those not linked to fields
    ).exclude(file_id__in=file_ids).delete()

    # Create new attachments
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
    Refreshes attachments for source.
    Creates new attachments for found file_ids.
    Removes unused attachments.
    Returns list of new file_ids.

    Supported types:
    - Task: extracts from description field
    - Workflow: extracts from description, kickoff_description
    - Template: extracts from description, kickoff_description
    - WorkflowEvent (comment): extracts from text field
    """
    # Determine source type and process
    if isinstance(source, Task):
        return _refresh_task_attachments(source, user)
    if isinstance(source, Workflow):
        return _refresh_workflow_attachments(source, user)
    if isinstance(source, Template):
        return _refresh_template_attachments(source, user)
    if isinstance(source, WorkflowEvent):
        return _refresh_workflow_event_attachments(source, user)
    return []


def _refresh_task_attachments(task: Task, user: UserModel) -> List[str]:
    """Refreshes attachments for task."""
    return refresh_attachments_for_text(
        account=task.account,
        user=user,
        text=task.description,
        source_type=SourceType.TASK,
        task=task,
    )


def _refresh_workflow_attachments(
        workflow: Workflow,
        user: UserModel,
) -> List[str]:
    """Refreshes attachments for workflow."""
    all_new_file_ids = []

    # Process workflow description only if present
    # Do not remove existing attachments when description is empty
    if workflow.description:
        new_file_ids = refresh_attachments_for_text(
            account=workflow.account,
            user=user,
            text=workflow.description,
            source_type=SourceType.WORKFLOW,
            workflow=workflow,
        )
        all_new_file_ids.extend(new_file_ids)

    # Process kickoff_description if present
    if hasattr(
            workflow,
            'kickoff_description',
    ) and workflow.kickoff_description:
        new_file_ids = refresh_attachments_for_text(
            account=workflow.account,
            user=user,
            text=workflow.kickoff_description,
            source_type=SourceType.WORKFLOW,
            workflow=workflow,
        )
        all_new_file_ids.extend(new_file_ids)

    # IMPORTANT: Do not remove attachments linked to fields (output != None)
    # They are managed separately via TaskFieldService

    # Re-assign permissions so new workflow members get access
    service = AttachmentService(user=user)
    for att in Attachment.objects.filter(
            workflow=workflow,
            access_type=AccessType.RESTRICTED,
    ):
        service.reassign_restricted_permissions(att)

    return list(set(all_new_file_ids))  # Deduplicate


def _refresh_template_attachments(
        template: Template,
        user: UserModel,
) -> List[str]:
    """Refreshes attachments for template."""
    all_new_file_ids = []

    # Process template description
    if template.description:
        new_file_ids = refresh_attachments_for_text(
            account=template.account,
            user=user,
            text=template.description,
            source_type=SourceType.TEMPLATE,
            template=template,
        )
        all_new_file_ids.extend(new_file_ids)

    # Process kickoff_description if present
    has_kickoff = hasattr(template, 'kickoff_description')
    if has_kickoff and template.kickoff_description:
        new_file_ids = refresh_attachments_for_text(
            account=template.account,
            user=user,
            text=template.kickoff_description,
            source_type=SourceType.TEMPLATE,
            template=template,
        )
        all_new_file_ids.extend(new_file_ids)

    # Re-assign permissions so new template owners get access
    service = AttachmentService(user=user)
    for att in Attachment.objects.filter(
            template=template,
            access_type=AccessType.RESTRICTED,
    ):
        service.reassign_restricted_permissions(att)

    return list(set(all_new_file_ids))  # Deduplicate


def _refresh_workflow_event_attachments(
        event: WorkflowEvent,
        user: UserModel,
) -> List[str]:
    """Refreshes attachments for workflow event (comment)."""
    # For workflow events attachments are always linked to event
    new_file_ids = refresh_attachments_for_event(
        account=event.account,
        user=user,
        text=event.text,
        event=event,
    )

    # Update with_attachments field for WorkflowEvent
    has_attachments = bool(extract_file_ids_from_text(event.text))
    if event.with_attachments != has_attachments:
        event.with_attachments = has_attachments
        event.save(update_fields=['with_attachments'])

    return new_file_ids


def get_attachment_description_fields(source: models.Model) -> List[str]:
    """
    Returns list of description fields for source.
    Used to find file_ids in various fields.
    """
    if isinstance(source, Task):
        return ['description']
    if isinstance(source, (Workflow, Template)):
        fields = ['description']
        if hasattr(source, 'kickoff_description'):
            fields.append('kickoff_description')
        return fields
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
