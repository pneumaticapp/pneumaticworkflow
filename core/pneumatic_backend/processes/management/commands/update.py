import re
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F

from pneumatic_backend.processes.models.workflows.event import WorkflowEvent
from pneumatic_backend.processes.models.workflows.fields import TaskField
from pneumatic_backend.processes.models.workflows.task import Task
from pneumatic_backend.processes.models.workflows.attachment import (
    FileAttachment
)
from pneumatic_backend.processes.enums import WorkflowEventType, FieldType
from pneumatic_backend.processes.api_v2.services.task.task import (
    TaskService
)
from pneumatic_backend.processes.api_v2.services.task.field import (
    TaskFieldService
)
from pneumatic_backend.services.markdown import (
    MarkdownPatterns
)


class Command(BaseCommand):

    def update_attacments(self):

        # Remove prefix from attachment names

        pattern = re.compile(r'\S{30}_(?P<filename>.+)')
        with transaction.atomic():
            for attachment in FileAttachment.objects.all():
                result = pattern.search(attachment.name)
                if result:
                    attachment.name = result['filename']
                    attachment.save(update_fields=['name'])

        print('Remove prefix from attachment names completed')

    def update_url_fields(self):

        # Update fields type file. Set markdown_value

        qst = (
            TaskField.objects
            .filter(type=FieldType.URL)
        )
        with transaction.atomic():
            for field in qst:
                if field.value in TaskFieldService.NULL_VALUES:
                    continue
                user = field.workflow.account.users.first()
                if not user:
                    continue
                service = TaskFieldService(instance=field, user=user)
                _, markdown_value = (
                    service._get_valid_url_value(raw_value=field.value)
                )
                field.markdown_value = markdown_value
                field.save(update_fields=['markdown_value'])

        print('Update fields type file. Set markdown_value completed!')

    def update_file_fields(self):

        # Update fields type file. Set markdown_value

        qst = (
            TaskField.objects
            .filter(type=FieldType.FILE)
            .select_related('workflow__account')
            .prefetch_related('attachments')
        )
        with transaction.atomic():
            for field in qst:
                if field.value in TaskFieldService.NULL_VALUES:
                    continue
                user = field.workflow.account.users.first()
                if not user:
                    continue
                service = TaskFieldService(instance=field, user=user)
                raw_value = [e.id for e in field.attachments.all()]
                _, markdown_value = (
                    service._get_valid_file_value(raw_value=raw_value)
                )
                field.markdown_value = markdown_value
                field.save(update_fields=['markdown_value'])

        print('Update fields type file. Set markdown_value completed!')

    def update_date_fields(self):

        # Update fields type file. Set markdown_value

        qst = (
            TaskField.objects
            .filter(type=FieldType.DATE)
            .select_related('workflow__account')
        )
        with transaction.atomic():
            for field in qst:
                if field.value in TaskFieldService.NULL_VALUES:
                    continue
                user = field.workflow.account.get_owner()
                if user is None:
                    continue
                service = TaskFieldService(instance=field, user=user)
                try:
                    _, markdown_value = (
                        service._get_valid_date_value(
                            raw_value=int(field.value)
                        )
                    )
                except ValueError as ex:
                    print(f'Field {field.id}. {ex}')
                field.markdown_value = markdown_value
                field.save(update_fields=['markdown_value'])

        print('Update fields type "Date". Set markdown_value completed!')

    def update_another_fields(self):

        # Update fields. Set markdown_value

        (
            TaskField.objects
            .exclude(type__in={FieldType.FILE, FieldType.URL, FieldType.DATE})
            .update(markdown_value=F('value'))
        )

    def update_tasks(self):

        # Update files markdown markup in tasks descriptions and checklists
        qst = (
            Task.objects
            .filter(description__isnull=False)
            .select_related('account', 'workflow')
            .exclude(date_started=None)
        )
        pattern = re.compile(r'\[(?P<fn_1>(?:\S{30}_)+(?P<fn_2>[^\]]+))]')

        with transaction.atomic():
            for task in qst:
                result = pattern.findall(task.description)
                if result:
                    for fn_1, fn_2 in result:
                        task.description = task.description.replace(fn_1, fn_2)
                user = task.account.get_owner()
                if not user:
                    print(f'User not found for task {task.id}')
                    continue
                service = TaskService(
                    instance=task,
                    user=user,
                    is_superuser=True
                )
                fields_values = task.workflow.get_fields_markdown_values(
                    tasks_filter_kwargs={'number__lt': task.number},
                )
                service.insert_fields_values(
                    fields_values=fields_values
                )
                task.save()

        print('Update tasks descriptions completed!')

    def update_comments(self):

        # Update comments
        # Remove prefix form filenames in the text
        # Set with_attachments flag if attachments in text
        # Link attachments to comment

        qst = (
            WorkflowEvent.objects
            .filter(type=WorkflowEventType.COMMENT)
            .filter(text__isnull=False)
            .exclude(text='')
        )
        media_pattern = MarkdownPatterns.MEDIA_PATTERN
        prefixed_filename_pattern = (
            re.compile(r'\[(?P<fn_1>(?:\S{30}_)+(?P<fn_2>[^\]]+))]')
        )

        with transaction.atomic():
            for event in qst:
                result = prefixed_filename_pattern.findall(event.text)
                if result:
                    for fn_1, fn_2 in result:
                        event.text = event.text.replace(fn_1, fn_2)

                attachments = media_pattern.findall(event.text)
                if attachments:
                    attachments_ids = [int(e) for e in attachments]
                    (
                        FileAttachment.objects
                        .on_account(event.account_id)
                        .by_ids(attachments_ids)
                        .update(event=event)
                    )
                    event.with_attachments = True
                else:
                    event.with_attachments = False
                event.save(update_fields=['with_attachments', 'text'])
        print('Update comments completed')

    def handle(self, *args, **options):
        # self.update_attacments()
        self.update_date_fields()
        # self.update_file_fields()
        self.update_url_fields()
        self.update_another_fields()
        self.update_tasks()
        # self.update_comments()
