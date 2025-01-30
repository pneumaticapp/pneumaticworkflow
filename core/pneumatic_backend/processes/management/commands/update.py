from django.db import transaction
from django.core.management.base import BaseCommand
from pneumatic_backend.processes.api_v2.serializers.workflow.events import (
    TaskEventJsonSerializer
)
from pneumatic_backend.processes.models import WorkflowEvent


class Command(BaseCommand):

    def handle(self, *args, **options):
        with transaction.atomic():
            qst = (
                WorkflowEvent.objects
                .prefetch_related(
                    'task',
                    'task__output',
                    'task__output__selections',
                    'task__output__attachments',
                )
                .filter(
                    type__in=(1, 2, 3, 4, 5, 8, 9, 13, 14, 15, 18),
                    task_json__isnull=True,
                    workflow_id=12399
                )
            )
            for event in qst:
                event.task_json = TaskEventJsonSerializer(
                    instance=event.task,
                    context={'event_type': event.type}
                ).data
                event.save(update_fields=['task_json'])
