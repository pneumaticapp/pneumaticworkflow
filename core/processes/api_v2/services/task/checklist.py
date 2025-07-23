from typing import Dict
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from pneumatic_backend.processes.models.templates.checklist import (
    ChecklistTemplate
)
from pneumatic_backend.processes.models import (
    Checklist,
    ChecklistSelection
)
from pneumatic_backend.processes.api_v2.services.task import exceptions
from pneumatic_backend.processes.api_v2.services.task\
    .checklist_selection import (
        ChecklistSelectionService,
    )
from pneumatic_backend.processes.api_v2.services.base import (
    BaseWorkflowService,
)


UserModel = get_user_model()


class ChecklistService(BaseWorkflowService):

    def _create_instance(
        self,
        instance_template: ChecklistTemplate,
        **kwargs
    ):
        self.instance = Checklist.objects.create(
            api_name=instance_template.api_name,
            task=kwargs['task']
        )

    def _create_related(
        self,
        instance_template: ChecklistTemplate,
        **kwargs
    ):
        for selection_template in instance_template.selections.all():
            selection_service = ChecklistSelectionService(user=self.user)
            selection_service.create(
                checklist=self.instance,
                instance_template=selection_template
            )

    def _get_selection(self, selection_id: int) -> ChecklistSelection:
        try:
            selection = ChecklistSelection.objects.prefetch_related(
                'checklist__task__workflow'
            ).get(
                checklist=self.instance,
                id=selection_id
            )
        except ObjectDoesNotExist:
            raise exceptions.ChecklistSelectionNotFound()
        return selection

    def insert_fields_values(
        self,
        fields_values: Dict[str, str],
    ):
        selections = []
        for selection in self.instance.selections.all():
            selection_service = ChecklistSelectionService(
                instance=selection,
                user=self.user
            )
            selection_service.insert_fields_values(fields_values)
            selections.append(selection_service.instance)
        ChecklistSelection.objects.bulk_update(selections, ['value'])

    def mark(
        self,
        selection_id: int
    ):
        selection = self._get_selection(selection_id)
        selection_service = ChecklistSelectionService(
            instance=selection,
            user=self.user
        )
        selection_service.mark()

    def unmark(
        self,
        selection_id: int
    ):
        selection = self._get_selection(selection_id)
        selection_service = ChecklistSelectionService(
            instance=selection,
            user=self.user
        )
        selection_service.unmark()
