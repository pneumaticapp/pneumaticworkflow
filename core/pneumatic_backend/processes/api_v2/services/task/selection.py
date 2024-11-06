from django.contrib.auth import get_user_model
from pneumatic_backend.processes.models import (
    FieldSelection,
    FieldTemplateSelection,
)
from pneumatic_backend.processes.api_v2.services.base import (
    BaseWorkflowService,
)


UserModel = get_user_model()


class SelectionService(BaseWorkflowService):

    def _create_related(
        self,
        instance_template: FieldTemplateSelection,
        **kwargs
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
            template_id=instance_template.id,
            api_name=instance_template.api_name,
            is_selected=kwargs['is_selected'],
        )
