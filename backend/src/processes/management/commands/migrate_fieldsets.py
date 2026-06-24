# ruff: noqa: T201 BLE001
from django.core.management.base import BaseCommand
from django.db import transaction
from src.processes.models.templates.fieldset import FieldsetTemplate
from src.processes.models.templates.template import TemplateDraft
from src.processes.services.fieldsets.fieldset import FieldSetTemplateService


class Command(BaseCommand):

    def get_drafts_by_fieldsets(self) -> dict:
        """
        Returns a dict where the key is fieldset api_name
        and the value is a list of template IDs that contain that fieldset.
        """
        result = {}

        for draft_obj in TemplateDraft.objects.all():
            draft = draft_obj.draft
            if not isinstance(draft, dict):
                continue

            # Process tasks -> fieldsets
            for task in draft.get('tasks') or []:
                for fieldset in task.get('fieldsets') or []:
                    if isinstance(fieldset, dict):
                        api_name = fieldset.get('api_name')
                        if api_name:
                            result.setdefault(api_name, set())
                            result[api_name].add(draft_obj.id)

            # Process kickoff -> fieldsets
            kickoff = draft.get('kickoff')
            if isinstance(kickoff, dict):
                for fieldset in kickoff.get('fieldsets') or []:
                    if isinstance(fieldset, dict):
                        api_name = fieldset.get('api_name')
                        if api_name:
                            result.setdefault(api_name, set())
                            result[api_name].add(draft_obj.id)

        return result

    def update_draft_fieldset(
        self,
        draft_id: int,
        fieldset_data: dict,
        fieldset_api_name: str,
        shared_fieldset_id: int,
    ):
        draft_obj = TemplateDraft.objects.get(id=draft_id)
        draft = draft_obj.draft
        if not isinstance(draft, dict):
            return

        updated = False

        # Update matching fieldsets in tasks
        for task in draft.get('tasks') or []:
            for fieldset in task.get('fieldsets') or []:
                if fieldset.get('api_name') == fieldset_api_name:
                    fieldset.update(fieldset_data)
                    fieldset['shared_fieldset_id'] = shared_fieldset_id
                    updated = True
                    print(
                        f'*** Draft {draft_id} '
                        f'(template {draft_obj.draft["name"]})'
                        f' - task "{task.get("name", "?")}"'
                        f' - fieldset "{fieldset_data["name"]}" updated',
                    )

        # Update matching fieldsets in kickoff
        kickoff = draft.get('kickoff')
        if isinstance(kickoff, dict):
            for fieldset in kickoff.get('fieldsets') or []:
                if fieldset.get('api_name') == fieldset_api_name:
                    fieldset.update(fieldset_data)
                    fieldset['shared_fieldset_id'] = shared_fieldset_id
                    updated = True
                    print(
                        f'*** Draft {draft_id} '
                        f'(template {draft_obj.draft["name"]})'
                        f' - kickoff'
                        f' - fieldset "{fieldset_data["name"]}" updated',
                    )

        if updated:
            draft_obj.save(update_fields=('draft',))
            print(f'  Draft {draft_id} saved')

    def handle(self, *args, **options):
        drafts_by_old_fieldsets = self.get_drafts_by_fieldsets()
        old_fieldsets = (
            FieldsetTemplate.objects
            .filter(is_shared=True)
            .order_by('account_id')
        )
        with transaction.atomic():
            for old_fieldset in old_fieldsets:
                # Ensure the original is marked as shared
                old_fieldset.template_id = None
                old_fieldset.is_shared = True

                # Build the serialized representation of the shared fieldset
                fieldset_data = FieldSetTemplateService.to_json(old_fieldset)
                fieldset_data.pop('id')
                fieldset_data.pop('api_name')
                fieldset_data.pop('order')
                shared_fieldset_data = (
                    FieldSetTemplateService._replace_api_names(fieldset_data)
                )
                old_fieldset.fields.delete()
                old_fieldset.rules.delete()
                user = old_fieldset.account.get_owner()

                shared_service = FieldSetTemplateService(user=user)
                shared_fieldset = shared_service.create(
                    is_shared=True,
                    **shared_fieldset_data,
                )
                print(
                    f'Shared - {shared_fieldset.name} : {shared_fieldset.id}',
                )

                # update drafts
                for draft_id in drafts_by_old_fieldsets.get(
                    old_fieldset.api_name, [],
                ):
                    self.update_draft_fieldset(
                        draft_id=draft_id,
                        fieldset_data=fieldset_data,
                        fieldset_api_name=old_fieldset.api_name,
                        shared_fieldset_id=shared_fieldset.id,
                    )

                kickoff_links = old_fieldset.kickoffs.through.objects.filter(
                    fieldset=old_fieldset,
                    is_deleted=False,
                )
                for link in kickoff_links:
                    if not FieldsetTemplate.objects.filter(
                        shared_fieldset_id=shared_fieldset.id,
                        is_shared=False,
                        kickoff_id=link.kickoff_id,
                    ).exists():
                        service = FieldSetTemplateService(user=user)
                        new_fs = service.create(
                            **fieldset_data,
                            is_shared=False,
                            shared_fieldset_id=shared_fieldset.id,
                            order=link.order,
                            kickoff_id=link.kickoff_id,
                            template_id=link.kickoff.template_id,
                        )
                        print(
                            f'+++ {link.kickoff.template.name} : '
                            f'{link.kickoff.template_id} - '
                            f'{new_fs.name} : {new_fs.id}',
                        )
                    link.delete()

                task_links = old_fieldset.tasks.through.objects.filter(
                    fieldset=old_fieldset,
                    is_deleted=False,
                )

                for link in task_links:
                    if not FieldsetTemplate.objects.filter(
                        shared_fieldset_id=shared_fieldset.id,
                        is_shared=False,
                        task_id=link.task_id,
                    ).exists():
                        service = FieldSetTemplateService(user=user)
                        try:
                            new_fs = service.create(
                                **fieldset_data,
                                is_shared=False,
                                shared_fieldset_id=shared_fieldset.id,
                                order=link.order,
                                task_id=link.task_id,
                                template_id=link.task.template_id,
                            )
                            print(
                                f'+++ {link.task.template.name} : '
                                f'{link.task.template_id} - '
                                f'{new_fs.name} : {new_fs.id}',
                            )
                        except Exception:
                            print(
                                f'--- Duplicate '
                                f'{link.task.template.name} : '
                                f'{link.task.template_id}',
                            )
                    link.delete()
                old_fieldset.delete()
