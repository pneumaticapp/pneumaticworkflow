from django.core.management.base import BaseCommand
from django.db import transaction
from pneumatic_backend.processes.utils.common import create_api_name
from pneumatic_backend.processes.models import TemplateDraft


class Command(BaseCommand):
    def update_draft(self):
        with transaction.atomic():
            template_drafts = TemplateDraft.objects.prefetch_related(
                'template__template_owners'
            ).filter(draft__owners__isnull=True)
            for draft_record in template_drafts:
                draft = draft_record.draft
                draft_template_owners = draft.get("template_owners", [])
                template_owners = {
                    e.user_id: e
                    for e in draft_record.template.owners.all()
                }
                owners = []
                for user_id in draft_template_owners:
                    template_owner = template_owners.get(int(user_id))
                    if template_owner:
                        owners.append({
                            "type": "user",
                            "api_name": template_owner.api_name,
                            "source_id": user_id
                        })
                    else:
                        owners.append({
                            "type": "user",
                            "api_name": create_api_name('owner'),
                            "source_id": user_id
                        })
                draft["owners"] = owners
                draft_record.draft = draft
                draft_record.save()
            print(template_drafts.count(), ' drafts update completed!')

    def handle(self, *args, **options):
        self.update_draft()
