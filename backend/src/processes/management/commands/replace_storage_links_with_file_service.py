import logging
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings

from src.accounts.models import (
    Account, User, Contact, UserGroup, Notification,
)
from src.processes.models.workflows.attachment import FileAttachment
from src.processes.models.workflows.event import WorkflowEvent
from src.processes.models.workflows.fields import TaskField
from src.processes.models.workflows.task import Task
from src.processes.models.workflows.workflow import Workflow
from src.processes.models.templates.template import Template, TemplateDraft
from src.processes.models.templates.task import TaskTemplate

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        'Replace storage links with file service links in all '
        'relevant fields'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--account-ids',
            type=str,
            required=True,
            help='Comma-separated list of account IDs',
        )
        parser.add_argument(
            '--file-service-domain',
            type=str,
            default='',
            help='Domain of file service',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Only show what would be updated',
        )
        parser.add_argument('--batch-size', type=int, default=100)

    def replace_in_json(self, obj, url_mapping):
        updated = False
        if isinstance(obj, str):
            for old_url, new_url in url_mapping.items():
                if old_url in obj:
                    obj = obj.replace(old_url, new_url)
                    updated = True
            return obj, updated
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_val, upd = self.replace_in_json(value, url_mapping)
                if upd:
                    obj[key] = new_val
                    updated = True
            return obj, updated
        if isinstance(obj, list):
            new_list = []
            for item in obj:
                new_item, upd = self.replace_in_json(item, url_mapping)
                if upd:
                    updated = True
                new_list.append(new_item)
            return new_list, updated
        return obj, updated

    def handle(self, *args, **options):
        account_ids = [
            int(x.strip())
            for x in options['account_ids'].split(',')
            if x.strip()
        ]
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        fs_domain = options['file_service_domain']

        if not fs_domain:
            fs_domain = getattr(settings, 'FILE_SERVICE_URL', None)
            if not fs_domain:
                raise CommandError(
                    "FILE_SERVICE_URL is not set in settings/environment.",
                )
        fs_domain = fs_domain.rstrip('/')

        if dry_run:
            self.stdout.write(self.style.WARNING(
                'DRY RUN: No actual links will be replaced.',
            ))

        # Build mapping
        url_mapping = {}
        # 1. Exact mapping of known attachments
        attachments = FileAttachment.objects.filter(
            account_id__in=account_ids,
            file_id__isnull=False,
        )
        for fa in attachments.iterator(chunk_size=batch_size):
            if fa.url:
                url_mapping[fa.url] = f"{fs_domain}/{fa.file_id}"
            if fa.thumbnail_url:
                url_mapping[fa.thumbnail_url] = f"{fs_domain}/{fa.file_id}"

        # 2. Add base bucket paths mapped to new fs_domain
        base_accounts = Account.objects.filter(id__in=account_ids)
        for account in base_accounts.iterator(chunk_size=batch_size):
            if account.bucket_name:
                url_mapping[
                    f"https://storage.googleapis.com/{account.bucket_name}"
                ] = fs_domain
                url_mapping[
                    f"https://storage.cloud.google.com/{account.bucket_name}"
                ] = fs_domain

        # 3. Add global bucket path just in case
        url_mapping[
            "https://storage.googleapis.com/pneumatic-bucket-dev"
        ] = fs_domain
        url_mapping[
            "https://storage.cloud.google.com/pneumatic-bucket-dev"
        ] = fs_domain

        self.stdout.write(
            f'Generated {len(url_mapping)} url mappings '
            f'(including base buckets). Commencing replacement...',
        )

        def process_text_fields(qs, fields):
            count = 0
            for item in qs.iterator(chunk_size=batch_size):
                item_updated = False
                for field in fields:
                    val = getattr(item, field, None)
                    if isinstance(val, str) and val:
                        for old_url, new_url in url_mapping.items():
                            if old_url in val:
                                val = val.replace(old_url, new_url)
                                item_updated = True
                        if item_updated:
                            setattr(item, field, val)

                if item_updated:
                    if not dry_run:
                        with transaction.atomic():
                            item.save(update_fields=fields)
                    count += 1
            return count

        def process_json_fields(qs, fields):
            count = 0
            for item in qs.iterator(chunk_size=batch_size):
                item_updated = False
                for field in fields:
                    val = getattr(item, field, None)
                    if val is not None:
                        new_val, upd = self.replace_in_json(val, url_mapping)
                        if upd:
                            setattr(item, field, new_val)
                            item_updated = True

                if item_updated:
                    if not dry_run:
                        with transaction.atomic():
                            item.save(update_fields=fields)
                    count += 1
            return count

        # 2. WorkflowEvent
        we_qs = WorkflowEvent.objects.filter(
            workflow__account_id__in=account_ids,
        )
        we_text_count = process_text_fields(we_qs, ['text', 'clear_text'])
        we_json_count = process_json_fields(we_qs, ['task_json'])
        self.stdout.write(
            f'Updated {we_text_count} WorkflowEvent (text), '
            f'{we_json_count} (json)',
        )

        # 3. TaskField
        # Note: Depending on where account_id is, TaskField belongs to
        # workflow which belongs to account
        tf_qs = TaskField.objects.filter(workflow__account_id__in=account_ids)
        tf_count = process_text_fields(
            tf_qs, ['value', 'clear_value', 'markdown_value'],
        )
        self.stdout.write(f'Updated {tf_count} TaskField records')

        # 4. Task
        task_qs = Task.objects.filter(workflow__account_id__in=account_ids)
        task_count = process_text_fields(
            task_qs,
            ['description', 'description_template', 'clear_description'],
        )
        self.stdout.write(f'Updated {task_count} Task records')

        # 4b. Workflow
        wf_qs = Workflow.objects.filter(account_id__in=account_ids)
        wf_count = process_text_fields(
            wf_qs,
            ['description', 'name', 'name_template', 'legacy_template_name'],
        )
        self.stdout.write(f'Updated {wf_count} Workflow records')

        # 4c. Notification
        notif_qs = Notification.objects.filter(
            user__account_id__in=account_ids,
        )
        notif_count_txt = process_text_fields(notif_qs, ['text'])
        notif_count_jsn = process_json_fields(notif_qs, ['task_json'])
        self.stdout.write(
            f'Updated {notif_count_txt} Notification (text), '
            f'{notif_count_jsn} (json)',
        )

        # 5. Template and TaskTemplate (TaskTemplate uses template)
        # We process Template.description, assuming TaskTemplate is part
        # of template or accessed via related manager
        template_qs = Template.objects.filter(account_id__in=account_ids)
        tmpl_count = process_text_fields(template_qs, ['description'])
        tt_qs = TaskTemplate.objects.filter(
            template__account_id__in=account_ids,
        )
        tt_count = process_text_fields(tt_qs, ['description'])
        self.stdout.write(
            f'Updated {tmpl_count} Template, {tt_count} TaskTemplate records',
        )

        # 7. TemplateDraft
        draft_qs = TemplateDraft.objects.filter(
            template__account_id__in=account_ids,
        )
        draft_count = process_json_fields(draft_qs, ['draft'])
        self.stdout.write(f'Updated {draft_count} TemplateDraft records')

        # 8-11. Logos and avatars
        acc_qs = Account.objects.filter(id__in=account_ids)
        acc_count = process_text_fields(acc_qs, ['logo_lg', 'logo_sm'])
        self.stdout.write(f'Updated {acc_count} Account records')

        usr_qs = User.objects.filter(account_id__in=account_ids)
        usr_count = process_text_fields(usr_qs, ['photo'])
        self.stdout.write(f'Updated {usr_count} User records')

        contact_qs = Contact.objects.filter(account_id__in=account_ids)
        contact_count = process_text_fields(contact_qs, ['photo'])
        self.stdout.write(f'Updated {contact_count} Contact records')

        group_qs = UserGroup.objects.filter(account_id__in=account_ids)
        group_count = process_text_fields(group_qs, ['photo'])
        self.stdout.write(f'Updated {group_count} UserGroup records')

        # 1. FileAttachment (direct properties) (Moved to end)
        fs_count = process_text_fields(attachments, ['url', 'thumbnail_url'])
        self.stdout.write(f'Updated {fs_count} FileAttachment records')

        self.stdout.write(self.style.SUCCESS(
            f'Done replacing links (Dry run: {dry_run})',
        ))
