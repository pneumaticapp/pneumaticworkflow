from django.core.management.base import BaseCommand

from src.storage.services.file_sync import FileSyncService


class Command(BaseCommand):
    """
    Command for synchronizing files between backend and file service.
    Creates file_id for existing FileAttachment without file_id.
    """

    help = 'Synchronize files between backend and file service'

    def handle(self, *args, **options):
        self.stdout.write('Starting file synchronization...')

        service = FileSyncService()
        stats = service.sync_all_files()

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSynchronization completed:\n"
                f"Total files: {stats['total']}\n"
                f"Synchronized: {stats['synced']}\n"
                f"Skipped: {stats['skipped']}\n"
                f"Errors: {stats['errors']}",
            ),
        )
