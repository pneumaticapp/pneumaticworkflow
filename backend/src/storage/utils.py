import re
from typing import List, Optional, Tuple

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models, transaction, IntegrityError

from src.storage.enums import AccessType, SourceType
from src.processes.models.templates.template import Template
from src.processes.models.workflows.event import WorkflowEvent
from src.processes.models.workflows.task import Task
from src.processes.models.workflows.workflow import Workflow
from src.storage.models import Attachment
from src.storage.services.attachments import (
    AttachmentService,
    clear_guardian_permissions_for_attachment_ids,
)

UserModel = get_user_model()


def _get_file_service_link_pattern(
        anchored: bool = False,
) -> Optional[re.Pattern]:
    """
    Build regex for file service markdown links;
    optional ^...$ for full match.
    Groups: (1) link label, (2) full URL, (3) file_id.
    """
    file_domain = settings.FILE_DOMAIN
    if not file_domain:
        return None
    core = (
        rf'\[([^\]]+)\]\('
        rf'(https?://[^/\s]*{re.escape(file_domain)}'
        rf'/([a-zA-Z0-9_-]{{8,64}})(?:[^\s)]*)?)\)'
    )
    if anchored:
        core = '^' + core + '$'
    return re.compile(core)


def _get_file_service_plain_url_pattern() -> Optional[re.Pattern]:
    """
    Build regex for a single plain file service URL (URLField value).
    Full string match: optional query/fragment after file_id.
    """
    file_domain = settings.FILE_DOMAIN
    if not file_domain:
        return None
    core = (
        rf'^https?://[^/\s]*{re.escape(file_domain)}'
        rf'/([a-zA-Z0-9_-]{{8,64}})(?:[^\s]*)?$'
    )
    return re.compile(core)


def _extract_file_id_from_plain_url(value: str) -> Optional[str]:
    """
    If value is a single file service URL (plain URLField-style),
    return its file_id; else None.
    """
    pattern = _get_file_service_plain_url_pattern()
    if pattern is None:
        return None
    match = pattern.match(value.strip())
    if match:
        return match.group(1)
    return None


def parse_single_file_service_link(text: str) -> Optional[Tuple[str, str]]:
    """
    Parse one markdown link to file service.

    Returns (full_url, file_id) if text is exactly one file service link,
    else None.
    """
    pattern = _get_file_service_link_pattern(anchored=True)
    if pattern is None:
        return None
    match = pattern.match(text.strip())
    if match:
        return (match.group(2), match.group(3))
    return None


def extract_file_ids_from_text(text: str) -> List[str]:
    """
    Extracts file_id from text for Pneumatic file service links.

    Searches for file service links in format:
    - Markdown links: [filename](url_with_file_id)

    Only extracts file_ids from file service domain (settings.FILE_DOMAIN).
    External links (Google Drive, Dropbox, etc.) are ignored.

    Args:
        text: Text content to search in

    Returns:
        List of unique file_ids from file service
    """
    pattern = _get_file_service_link_pattern(anchored=False)
    if not text or pattern is None:
        return []
    matches = pattern.findall(text)
    file_ids = [m[2] for m in matches]
    return list(dict.fromkeys(file_ids))


def extract_file_ids_from_values(
    values: List[Optional[str]],
) -> List[str]:
    """
    Extracts file_ids from list of text values.

    Handles both:
    - Plain file service URLs (URLField: logo, photo, etc.)
    - Text with Markdown file service links.
    """
    file_ids = []
    for value in values:
        if not value:
            continue
        plain_id = _extract_file_id_from_plain_url(value)
        if plain_id is not None:
            file_ids.append(plain_id)
        else:
            file_ids.extend(extract_file_ids_from_text(value))
    return list(dict.fromkeys(file_ids))


def get_file_service_file_url(file_id: str) -> Optional[str]:
    """
    Returns full URL to file in file service for download/display.
    Format: {FILE_SERVICE_URL}/{file_id}.
    """
    base = getattr(settings, 'FILE_SERVICE_URL', None)
    if not base or not file_id:
        return None
    return f"{base.rstrip('/')}/{file_id}"


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
        to_delete = Attachment.objects.filter(
            file_id__in=remove_file_ids,
            **filter_kwargs,
        )
        ids_to_delete = list(to_delete.values_list('id', flat=True))
        clear_guardian_permissions_for_attachment_ids(ids_to_delete)
        to_delete.delete()
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
) -> Tuple[List[str], bool]:
    """
    Refreshes attachments for workflow event (comment).

    Args:
        account: Account
        user: User
        text: Text to analyze
        event: Workflow event

    Returns:
        (new_file_ids, has_attachments). has_attachments reflects DB state
        after refresh (or after rollback on exception).
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
        to_delete = Attachment.objects.filter(**filter_kwargs)
        ids_to_delete = list(to_delete.values_list('id', flat=True))
        clear_guardian_permissions_for_attachment_ids(ids_to_delete)
        to_delete.delete()
        return [], False

    # Get existing file_ids
    existent_file_ids = list(
        Attachment.objects.filter(
            file_id__in=file_ids,
            **filter_kwargs,
        ).values_list('file_id', flat=True),
    )

    # Delete then create in one transaction; rollback on create failure
    new_files_ids = list(set(file_ids) - set(existent_file_ids))
    try:
        with transaction.atomic():
            to_delete = Attachment.objects.filter(
                **filter_kwargs,
            ).exclude(file_id__in=file_ids)
            ids_to_delete = list(to_delete.values_list('id', flat=True))
            clear_guardian_permissions_for_attachment_ids(ids_to_delete)
            to_delete.delete()
            if new_files_ids:
                service = AttachmentService(user=user)
                service.bulk_create_for_event(
                    file_ids=new_files_ids,
                    account=account,
                    source_type=source_type,
                    event=event,
                )
    except (ValueError, TypeError, IntegrityError):
        return [], bool(existent_file_ids)
    return new_files_ids, True


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
    # Only scope (description) attachments; exclude event (comment) ones
    filter_kwargs['event__isnull'] = True

    # If no files in text - delete only attachments not linked to fields
    if not file_ids:
        # Do not delete attachments linked to fields (output != None)
        to_delete = Attachment.objects.filter(
            **filter_kwargs,
            output__isnull=True,  # Delete only those not linked to fields
        )
        ids_to_delete = list(to_delete.values_list('id', flat=True))
        clear_guardian_permissions_for_attachment_ids(ids_to_delete)
        to_delete.delete()
        return []

    # Get existing file_ids
    existent_file_ids = list(
        Attachment.objects.filter(
            file_id__in=file_ids,
            **filter_kwargs,
        ).values_list('file_id', flat=True),
    )

    # Delete then create in one transaction; rollback on create failure
    new_files_ids = list(set(file_ids) - set(existent_file_ids))
    try:
        with transaction.atomic():
            to_delete = Attachment.objects.filter(
                **filter_kwargs,
                output__isnull=True,  # Delete only those not linked to fields
            ).exclude(file_id__in=file_ids)
            ids_to_delete = list(to_delete.values_list('id', flat=True))
            clear_guardian_permissions_for_attachment_ids(ids_to_delete)
            to_delete.delete()
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
    except (ValueError, TypeError, IntegrityError):
        return []
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


def _get_kickoff_description_text(source) -> str:
    """
    Returns kickoff description text for workflow or template.
    Workflow: KickoffValue.clear_description.
    Template: concatenation of kickoff field descriptions.
    """
    if isinstance(source, Workflow):
        kickoff_inst = getattr(source, 'kickoff_instance', None)
        if kickoff_inst is None:
            return ''
        return getattr(kickoff_inst, 'clear_description', None) or ''
    if isinstance(source, Template):
        kickoff_inst = getattr(source, 'kickoff_instance', None)
        if kickoff_inst is None:
            return ''
        fields = getattr(kickoff_inst, 'fields', None)
        if fields is None:
            return ''
        parts = [
            getattr(f, 'description', None) or ''
            for f in fields.all()
        ]
        return '\n'.join(parts)
    return ''


def _refresh_workflow_attachments(
        workflow: Workflow,
        user: UserModel,
) -> List[str]:
    """Refreshes attachments for workflow (description + kickoff)."""
    description = workflow.description or ''
    kickoff = _get_kickoff_description_text(workflow)
    combined_text = f'{description}\n{kickoff}'

    all_new_file_ids = refresh_attachments_for_text(
        account=workflow.account,
        user=user,
        text=combined_text,
        source_type=SourceType.WORKFLOW,
        workflow=workflow,
    )

    # IMPORTANT: Do not remove attachments linked to fields (output != None)
    # They are managed separately via TaskFieldService

    # Re-assign permissions so new workflow members get access
    service = AttachmentService(user=user)
    for att in Attachment.objects.filter(
            workflow=workflow,
            access_type=AccessType.RESTRICTED,
    ):
        service.reassign_restricted_permissions(att)

    return list(set(all_new_file_ids))


def _refresh_template_attachments(
        template: Template,
        user: UserModel,
) -> List[str]:
    """Refreshes attachments for template (description + kickoff)."""
    description = template.description or ''
    kickoff = _get_kickoff_description_text(template)
    combined_text = f'{description}\n{kickoff}'

    all_new_file_ids = refresh_attachments_for_text(
        account=template.account,
        user=user,
        text=combined_text,
        source_type=SourceType.TEMPLATE,
        template=template,
    )

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
    new_file_ids, has_attachments = refresh_attachments_for_event(
        account=event.account,
        user=user,
        text=event.text,
        event=event,
    )
    if event.with_attachments != has_attachments:
        event.with_attachments = has_attachments
        event.save(update_fields=['with_attachments'])
    return new_file_ids


def reassign_restricted_permissions_for_task(
    task: Task,
    user: UserModel,
) -> None:
    """
    Reassign restricted permissions for all attachments linked to task.
    Call after task performers change so new performers get access.
    """
    service = AttachmentService(user=user)
    for att in Attachment.objects.filter(
            task=task,
            access_type=AccessType.RESTRICTED,
    ):
        service.reassign_restricted_permissions(att)


def get_attachment_description_fields(source: models.Model) -> List[str]:
    """
    Returns list of description fields for source.
    Used to find file_ids in various fields.
    """
    if isinstance(source, Task):
        return ['description']
    if isinstance(source, (Workflow, Template)):
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

    if isinstance(source, (Workflow, Template)):
        kickoff_text = _get_kickoff_description_text(source)
        if kickoff_text:
            all_file_ids.extend(extract_file_ids_from_text(kickoff_text))

    return list(set(all_file_ids))
