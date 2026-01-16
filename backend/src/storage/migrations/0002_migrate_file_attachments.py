# Migration for data transfer from FileAttachment to Attachment

from django.db import migrations


def migrate_file_attachments(apps, schema_editor):
    """
    Transfers data from FileAttachment to Attachment.
    Determines source_type based on relations.
    """
    FileAttachment = apps.get_model('processes', 'FileAttachment')
    Attachment = apps.get_model('storage', 'Attachment')

    # Get only FileAttachment with file_id
    file_attachments = FileAttachment.objects.filter(
        file_id__isnull=False
    ).select_related('account', 'workflow', 'event', 'output')

    attachments_to_create = []

    for old_attachment in file_attachments:
        # Determine source_type
        source_type = determine_source_type(old_attachment)

        # Determine task
        task = get_task_from_attachment(old_attachment)

        # Create new attachment
        new_attachment = Attachment(
            file_id=old_attachment.file_id,
            access_type=old_attachment.access_type,
            source_type=source_type,
            account=old_attachment.account,
            task=task,
            workflow=old_attachment.workflow,
            template=None,
            is_deleted=old_attachment.is_deleted,
        )
        attachments_to_create.append(new_attachment)

    # Bulk create
    if attachments_to_create:
        Attachment.objects.bulk_create(
            attachments_to_create,
            ignore_conflicts=True
        )


def determine_source_type(attachment):
    """Determines source_type based on relations."""
    if attachment.workflow and not attachment.event:
        return 'Workflow'
    elif attachment.event:
        if hasattr(attachment.event, 'task') and attachment.event.task:
            return 'Task'
        else:
            return 'Workflow'
    elif attachment.output:
        return 'Task'
    else:
        return 'Account'


def get_task_from_attachment(attachment):
    """Gets task from attachment."""
    if attachment.event:
        if hasattr(attachment.event, 'task'):
            return attachment.event.task
    elif attachment.output:
        if hasattr(attachment.output, 'task'):
            return attachment.output.task
    return None


def reverse_migration(apps, schema_editor):
    """Rollback migration - deletes all Attachment records."""
    Attachment = apps.get_model('storage', 'Attachment')
    Attachment.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('storage', '0001_initial'),
        ('processes', '__latest__'),
    ]

    operations = [
        migrations.RunPython(
            migrate_file_attachments,
            reverse_migration
        ),
    ]

