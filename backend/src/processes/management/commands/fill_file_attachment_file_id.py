import logging
from urllib.parse import urlparse, unquote

from django.core.management.base import BaseCommand
from django.db import transaction

from src.processes.models.workflows.attachment import FileAttachment

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        'Fill file_id in FileAttachment from URL for legacy Google Cloud '
        'Storage URLs for specific accounts'
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

    def handle(self, *args, **options):
        account_ids = [
            int(x.strip())
            for x in options['account_ids'].split(',')
            if x.strip()
        ]
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING(
                'DRY RUN: No changes will be applied to the database.',
            ))

        attachments = FileAttachment.objects.filter(
            file_id__isnull=True,
            account_id__in=account_ids,
        ).select_related('account')

        total = attachments.count()
        self.stdout.write(
            f'Found {total} attachments without file_id for the given '
            f'accounts.',
        )

        updated = 0
        skipped = 0
        errors = 0

        for attachment in attachments:
            if not attachment.url:
                skipped += 1
                continue

            try:
                parsed = urlparse(attachment.url)
                if parsed.netloc not in (
                    'storage.googleapis.com', 'storage.cloud.google.com',
                ):
                    skipped += 1
                    continue

                path_parts = parsed.path.lstrip('/').split('/', 1)
                if len(path_parts) != 2:
                    skipped += 1
                    continue

                # object_key format: <prefix>_<original_filename>
                object_key = unquote(path_parts[1])

                if not dry_run:
                    with transaction.atomic():
                        attachment.file_id = object_key
                        attachment.save(update_fields=['file_id'])

                updated += 1

                if updated % 100 == 0:
                    self.stdout.write(
                        f'Processed {updated} / {total} attachments...',
                    )

            except Exception as e:  # noqa: BLE001
                logger.error(
                    "Error processing attachment %s: %s",
                    attachment.id, e,
                )
                errors += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done. Updated: {updated}, Skipped: {skipped}, Errors: {errors} '
            f'(Dry run: {dry_run})',
        ))
