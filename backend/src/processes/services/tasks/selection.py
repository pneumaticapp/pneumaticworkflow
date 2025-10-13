from django.contrib.auth import get_user_model
from src.processes.models.workflows.fields import FieldSelection
from src.processes.models.templates.fields import FieldTemplateSelection
from src.processes.services.base import (
    BaseWorkflowService,
)


UserModel = get_user_model()


class SelectionService(BaseWorkflowService):

    def _create_related(
        self,
        instance_template: FieldTemplateSelection,
        **kwargs,
    ):
        pass

    def _create_instance(
        self,
        instance_template: FieldTemplateSelection,
        **kwargs,
    ):
        self.instance = FieldSelection.objects.create(
            field_id=kwargs['field_id'],
            value=instance_template.value,
            api_name=instance_template.api_name,
            is_selected=kwargs['is_selected'],
        )
