from django.core.management.base import BaseCommand
from django.db import transaction
from src.processes.models.templates.preset import TemplatePresetField


class Command(BaseCommand):

    help = 'Set more unique api_names for system columns.'

    def handle(self, *args, **options):
        with transaction.atomic():
            (
                TemplatePresetField.objects
                .filter(api_name='workflow')
                .update(api_name='system-column-workflow')
            )
            (
                TemplatePresetField.objects
                .filter(api_name='starter')
                .update(api_name='system-column-starter')
            )
            (
                TemplatePresetField.objects
                .filter(api_name='progress')
                .update(api_name='system-column-progress')
            )
            (
                TemplatePresetField.objects
                .filter(api_name='step')
                .update(api_name='system-column-step')
            )
            (
                TemplatePresetField.objects
                .filter(api_name='performer')
                .update(api_name='system-column-performer')
            )
            (
                TemplatePresetField.objects
                .filter(api_name='template')
                .update(api_name='system-column-template')
            )
