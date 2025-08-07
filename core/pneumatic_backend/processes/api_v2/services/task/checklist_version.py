from typing import Tuple
from django.contrib.auth import get_user_model
from pneumatic_backend.processes.models import (
    Checklist,
)
from pneumatic_backend.processes.api_v2.services.task\
    .checklist_selection import (
        ChecklistSelectionVersionService,
    )
from pneumatic_backend.processes.api_v2.services.base import (
    BaseUpdateVersionService,
)


UserModel = get_user_model()


class ChecklistUpdateVersionService(BaseUpdateVersionService):

    def update_from_version(
        self,
        data: dict,
        version: int,
        **kwargs
    ) -> Tuple[Checklist, bool]:

        """
            data = {
                'api_name': str,
                'selections': str,
            }
        """

        self.instance, created = Checklist.objects.update_or_create(
            task=kwargs['task'],
            api_name=data['api_name']
        )
        for selection_data in data['selections']:
            selection_service = ChecklistSelectionVersionService(
                user=self.user,
                is_superuser=self.is_superuser,
                auth_type=self.auth_type
            )
            selection_service.update_from_version(
                data=selection_data,
                version=version,
                checklist=self.instance,
                fields_values=kwargs['fields_values']
            )
        if not created:
            api_names = {elem['api_name'] for elem in data['selections']}
            self.instance.selections.exclude(api_name__in=api_names).delete()
        return self.instance, created
