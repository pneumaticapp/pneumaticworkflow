import logging
from django.core.management.base import BaseCommand
from django.db import transaction

from src.processes.models.workflows.attachment import FileAttachment
from src.storage.enums import AccessType, SourceType
from src.storage.models import Attachment

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Migrates FileAttachment data to Attachment data'

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
            file_id__isnull=False,
            account_id__in=account_ids,
        ).select_related(
            'workflow',
            'event',
            'event__task',
            'event__task__workflow',
            'output',
            'output__workflow',
        )

        total = attachments.count()
        self.stdout.write(
            f'Found {total} FileAttachments to migrate for provided accounts.',
        )

        created = 0
        skipped = 0
        errors = 0

        for attr in attachments:
            try:
                if Attachment.objects.filter(file_id=attr.file_id).exists():
                    skipped += 1
                    continue

                access_type = AccessType.ACCOUNT
                if attr.workflow_id or attr.event_id or attr.output_id:
                    access_type = AccessType.RESTRICTED

                source_type = SourceType.ACCOUNT

                task_id = None
                if attr.event_id and attr.event.task_id:
                    task_id = attr.event.task_id
                elif attr.output_id and attr.output.task_id:
                    task_id = attr.output.task_id

                template_id = None
                if attr.workflow_id:
                    template_id = attr.workflow.template_id
                elif (
                    attr.event_id and
                    attr.event.task_id and
                    attr.event.task.workflow_id
                ):
                    template_id = attr.event.task.workflow.template_id
                elif attr.output_id and attr.output.workflow_id:
                    template_id = attr.output.workflow.template_id

                if not dry_run:
                    with transaction.atomic():
                        Attachment.objects.create(
                            file_id=attr.file_id,
                            access_type=access_type,
                            source_type=source_type,
                            account_id=attr.account_id,
                            template_id=template_id,
                            task_id=task_id,
                            workflow_id=attr.workflow_id,
                            event_id=attr.event_id,
                            output_id=attr.output_id,
                        )
                created += 1

                if (created + skipped) % 100 == 0:
                    self.stdout.write(
                        f'Processed {created + skipped} / {total} '
                        f'attachments...',
                    )

            except Exception as e:  # noqa: BLE001
                logger.error(
                    "Error creating Attachment for file_id %s: %s",
                    attr.file_id, e,
                )
                errors += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done. Created: {created}, Skipped: {skipped}, Errors: {errors} '
            f'(Dry run: {dry_run})',
        ))
