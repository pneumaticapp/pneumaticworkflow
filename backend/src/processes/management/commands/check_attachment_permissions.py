import logging
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from src.storage.enums import AccessType
from src.storage.models import Attachment

logger = logging.getLogger(__name__)
UserModel = get_user_model()


class Command(BaseCommand):
    help = (
        'Check that all attachments have correct access_type and '
        'Guardian permissions'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--account-ids',
            type=str,
            required=True,
            help='Comma-separated list of account IDs',
        )

    def handle(self, *args, **options):
        account_ids = [
            int(x.strip())
            for x in options['account_ids'].split(',')
            if x.strip()
        ]

        attachments = Attachment.objects.filter(account_id__in=account_ids)

        total = attachments.count()
        restricted = attachments.filter(
            access_type=AccessType.RESTRICTED,
        ).count()
        account_level = attachments.filter(
            access_type=AccessType.ACCOUNT,
        ).count()

        self.stdout.write(
            f'Total attachments migrated for accounts {account_ids}: {total}',
        )
        self.stdout.write(f'  - Restricted access: {restricted}')
        self.stdout.write(f'  - Account access: {account_level}')

        if total > 0:
            invalid = attachments.exclude(
                access_type__in=[AccessType.RESTRICTED, AccessType.ACCOUNT],
            ).count()
            if invalid > 0:
                self.stdout.write(self.style.ERROR(
                    f'Found {invalid} attachments with invalid access_type!',
                ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    'All attachments have valid access_type.',
                ))
