# ruff: noqa: T201
import copy

from django.core.management.base import BaseCommand
from django.db import transaction
from src.processes.models.templates.fieldset import FieldsetTemplate
from src.processes.models.templates.template import TemplateDraft
from src.processes.services.fieldsets.fieldset import FieldSetTemplateService


class Command(BaseCommand):

    def update_draft_fieldset(
        self,
        template_draft: TemplateDraft,
        fieldset_data: dict,
        fieldset_api_name: str,
    ):
        draft = template_draft.draft
        if not isinstance(draft, dict):
            return

        print('--- update template draft')
        updated = False
        # Update matching fieldsets in kickoff
        kickoff = draft.get('kickoff')
        new_kickoff_fieldsets = []
        if isinstance(kickoff, dict):
            kickoff_fieldsets = kickoff.get('fieldsets') or []
            for i in range(len(kickoff_fieldsets)):
                api_name = kickoff_fieldsets[i].get('api_name')
                if api_name == fieldset_api_name:
                    if not updated:
                        new_kickoff_fieldsets.append(fieldset_data)
                        print('---|--- new kickoff fieldset')
                        updated = True
                    else:
                        print('---|--- duplicate kickoff fieldset - removed')
                else:
                    new_kickoff_fieldsets.append(kickoff_fieldsets[i])
            kickoff['fieldsets'] = new_kickoff_fieldsets

        # Update matching fieldsets in tasks
        for task in draft.get('tasks') or []:
            new_task_fieldsets = []
            task_fieldsets = task.get('fieldsets') or []
            for i in range(len(task_fieldsets)):
                api_name = task_fieldsets[i].get('api_name')
                if api_name == fieldset_api_name:
                    if not updated:
                        task_fieldsets.append(fieldset_data)
                        print(
                            f'---|--- new task fieldset: '
                            f'task: "{task["name"]}"',
                        )
                        updated = True
                    else:
                        print('---|--- duplicate kickoff fieldset - removed')
                        del task_fieldsets[i]
                else:
                    new_task_fieldsets.append(task_fieldsets[i])
            task['fieldsets'] = new_kickoff_fieldsets
        template_draft.save(update_fields=('draft',))

    def handle(self, *args, **options):
        old_fieldsets = (
            FieldsetTemplate.objects
            .filter(is_shared=True)
            .exclude(template_id=None)
            .order_by('account_id')
        )
        with transaction.atomic():
            for old_shared_fieldset in old_fieldsets:
                print(
                    f'\nProcessed old shared fieldset: '
                    f'{old_shared_fieldset.name} ({old_shared_fieldset.id})',
                )
                template = old_shared_fieldset.template
                if template.is_active:
                    template_draft = None
                    print('--- template is active')
                else:
                    template_draft = template.draft
                    print('--- template not active')

                # Ensure the original is marked as shared
                old_shared_fieldset.template_id = None

                # Build the serialized representation of the shared fieldset
                old_shared_fieldset_data = FieldSetTemplateService.to_json(
                    old_shared_fieldset,
                )
                template_fieldset_data = copy.deepcopy(
                    old_shared_fieldset_data,
                )

                old_shared_fieldset_data.pop('id')
                old_shared_fieldset_data.pop('api_name')
                old_shared_fieldset_data.pop('order')
                # Recreate shared fieldset with new api_names
                new_shared_fieldset_data = (
                    FieldSetTemplateService._replace_api_names(
                        old_shared_fieldset_data,
                    )
                )
                old_shared_fieldset.fields.all().delete()
                old_shared_fieldset.rules.all().delete()
                user = old_shared_fieldset.account.get_owner()

                shared_service = FieldSetTemplateService(user=user)
                new_shared_fieldset = shared_service.create_shared_fieldset(
                    **new_shared_fieldset_data,
                )
                template_fieldset_data['shared_fieldset_id'] = (
                    new_shared_fieldset.id
                )
                template_fieldset_data.pop('order', None)
                print(f'--- new shared fieldset id: {new_shared_fieldset.id}')

                # update drafts
                if template_draft:
                    self.update_draft_fieldset(
                        template_draft=template_draft,
                        fieldset_data=template_fieldset_data,
                        fieldset_api_name=old_shared_fieldset.api_name,
                    )

                updated = False
                # update kickoff fieldsets
                kickoff_links = (
                    old_shared_fieldset.kickoffs
                    .through.objects.filter(
                        fieldset=old_shared_fieldset,
                        is_deleted=False,
                    )
                )
                for link in kickoff_links:
                    if not updated:
                        service = FieldSetTemplateService(user=user)
                        new_template_fieldset = service.create(
                            **template_fieldset_data,
                            is_shared=False,
                            order=link.order,
                            kickoff_id=link.kickoff_id,
                            template_id=link.kickoff.template_id,
                        )
                        updated = True
                        print(
                            f'--- new kickoff fieldset: '
                            f'{new_template_fieldset.id}. '
                            f'template: {link.kickoff.template.name} '
                            f'({link.kickoff.template_id})',
                        )
                    else:
                        print('--- duplicate kickoff fieldset - removed')
                    link.delete()

                # update tasks fieldsets
                task_links = old_shared_fieldset.tasks.through.objects.filter(
                    fieldset=old_shared_fieldset,
                    is_deleted=False,
                )

                for link in task_links:
                    if not updated:
                        service = FieldSetTemplateService(user=user)
                        new_template_fieldset = service.create(
                            **template_fieldset_data,
                            is_shared=False,
                            order=link.order,
                            task_id=link.task_id,
                            template_id=link.task.template_id,
                        )
                        updated = True
                        print(
                            f'--- new task fieldset: '
                            f'{new_template_fieldset.id}. '
                            f'task: "{link.task.name}" '
                            f'({link.task.id})',
                        )
                    else:
                        print('--- duplicate task fieldset - removed')
                    link.delete()
                old_shared_fieldset.delete()
