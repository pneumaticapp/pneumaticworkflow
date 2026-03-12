import logging
import mimetypes
import psycopg2
from datetime import datetime, timezone

from django.core.management.base import BaseCommand
from django.conf import settings
from src.processes.models.workflows.attachment import FileAttachment
from src.storage.models import Attachment

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        'Synchronize data from FileAttachment to FileRecordORM '
        '(via psycopg2)'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--account-ids',
            type=str,
            required=True,
            help='Comma-separated list of account IDs',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Only show what would be updated',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Batch size for db insertion',
        )

    def get_file_db_connection(self):
        db_name = settings.FILE_POSTGRES_DB
        user = settings.FILE_POSTGRES_USER
        password = settings.FILE_POSTGRES_PASSWORD
        host = settings.FILE_POSTGRES_HOST
        port = settings.FILE_POSTGRES_PORT

        if not all([db_name, user, password, host, port]):
            raise psycopg2.OperationalError(
                "FILE_POSTGRES_* config missing in environment/settings.",
            )

        try:
            return psycopg2.connect(
                dbname=db_name,
                user=user,
                password=password,
                host=host,
                port=port,
            )
        except psycopg2.OperationalError:
            self.stdout.write(self.style.WARNING(
                f"Failed to connect to {host}:{port}.",
            ))
            return psycopg2.connect(
                dbname=db_name,
                user=user,
                password=password,
                host='localhost',
                port='5433',
            )

    def handle(self, *args, **options):
        account_ids = [
            int(x.strip())
            for x in options['account_ids'].split(',')
            if x.strip()
        ]
        dry_run = options['dry_run']
        batch_size = options['batch_size']

        if dry_run:
            self.stdout.write(self.style.WARNING(
                'DRY RUN: No actual sync to file DB will occur.',
            ))

        valid_file_ids = Attachment.objects.filter(
            account_id__in=account_ids,
        ).values_list('file_id', flat=True)
        attachments = FileAttachment.objects.filter(
            file_id__in=valid_file_ids,
            account_id__in=account_ids,
        ).select_related('account')

        total = attachments.count()
        self.stdout.write(f'Found {total} records ready to be synced.')

        try:
            if not dry_run:
                conn = self.get_file_db_connection()
                cursor = conn.cursor()

                # Check if the table exists
                cursor.execute(
                    "SELECT EXISTS (SELECT FROM information_schema.tables "
                    "WHERE table_name = 'files');",
                )
                table_exists = cursor.fetchone()[0]

                if not table_exists:
                    self.stdout.write(self.style.ERROR(
                        "The 'files' table does not exist in the file "
                        "database! Please ensure the file service migrations "
                        "are already applied.",
                    ))
                    return
        except psycopg2.Error as e:
            self.stdout.write(self.style.ERROR(
                f"Could not connect to file database: {e}",
            ))
            return

        synced = 0
        skipped = 0
        errors = 0

        for attr in attachments.iterator(chunk_size=batch_size):
            file_id = attr.file_id
            size = attr.size if attr.size else 0
            filename = attr.name or "unnamed"

            content_type, _ = mimetypes.guess_type(filename)
            if not content_type:
                content_type = 'application/octet-stream'

            user_id = None
            if attr.account_id:
                owner = attr.account.get_owner()
                user_id = owner.id if owner else None

            created_at = datetime.now(timezone.utc)

            if not dry_run:
                try:
                    cursor.execute(
                        "SELECT file_id FROM files WHERE file_id = %s",
                        (file_id,),
                    )
                    if cursor.fetchone() is not None:
                        skipped += 1
                        continue

                    insert_query = """
                        INSERT INTO files
                        (file_id, size, content_type, filename, user_id,
                         account_id, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(insert_query, (
                        file_id, size, content_type, filename, user_id,
                        attr.account_id, created_at,
                    ))
                    synced += 1

                    if synced % batch_size == 0:
                        conn.commit()
                        self.stdout.write(
                            f'Synced {synced} / {total} records...',
                        )

                except psycopg2.Error as e:
                    logger.error("Error syncing %s: %s", file_id, e)
                    conn.rollback()
                    errors += 1
            else:
                synced += 1

        if not dry_run:
            conn.commit()
            cursor.close()
            conn.close()

        self.stdout.write(self.style.SUCCESS(
            f'Done. Synced: {synced}, Skipped: {skipped}, Errors: {errors} '
            f'(Dry run: {dry_run})',
        ))
