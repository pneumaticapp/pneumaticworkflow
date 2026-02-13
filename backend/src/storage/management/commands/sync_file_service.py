from django.core.management.base import BaseCommand

from src.storage.services.file_sync import FileSyncService


class Command(BaseCommand):
    """
    Command for synchronizing files between backend and file service
    and Attachment records to storage.
    Creates file_id for FileAttachment without file_id;
    syncs FileAttachment to Attachment model.

    Command: python manage.py sync_file_service
    """

    help = (
        'Synchronize files with file service and attachments to storage'
    )

    def handle(self, *args, **options):
        self.stdout.write('Starting file synchronization...')

        service = FileSyncService()
        file_service_stats = service.sync_all_files()
        storage_stats = service.sync_all_attachments_to_storage()

        self.stdout.write(
            self.style.SUCCESS(
                "\nFile service synchronization:\n"
                f"  Total: {file_service_stats['total']}\n"
                f"  Synced: {file_service_stats['synced']}\n"
                f"  Skipped: {file_service_stats['skipped']}\n"
                f"  Errors: {file_service_stats['errors']}\n"
                "\nStorage (Attachment) synchronization:\n"
                f"  Total: {storage_stats['total']}\n"
                f"  Created: {storage_stats['created']}\n"
                f"  Skipped: {storage_stats['skipped']}\n"
                f"  Errors: {storage_stats['errors']}",
            ),
        )
