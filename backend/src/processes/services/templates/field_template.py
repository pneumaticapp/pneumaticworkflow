from typing import Optional

from django.db.models import Model

from src.generics.base.service import BaseModelService
from src.processes.enums import FieldType
from src.processes.models.templates.fields import FieldTemplate
from src.processes.services.exceptions import (
    FieldTemplateSelectionsRequired,
    FieldTemplateUserMustBeRequired,
)
from src.processes.services.templates.field_template_selection import (
    FieldTemplateSelectionService,
)


class FieldTemplateService(BaseModelService):

    def _validate(self, **kwargs):
        field_type = kwargs.get('type')

        if (
            field_type in FieldType.TYPES_WITH_SELECTIONS
            and not (kwargs.get('selections') or kwargs.get('dataset'))
        ):
            raise FieldTemplateSelectionsRequired

        if field_type == FieldType.USER and kwargs.get('is_required') is False:
            raise FieldTemplateUserMustBeRequired

    def create(self, **kwargs) -> Model:
        self._validate(**kwargs)
        return super().create(**kwargs)

    def partial_update(self, **update_kwargs) -> Model:
        self._validate(**update_kwargs)
        return super().partial_update(**update_kwargs)

    def _create_instance(
        self,
        name: str,
        type: str,  # noqa: A002
        order: int = 0,
        description: str = '',
        is_required: bool = False,
        is_hidden: bool = False,
        default: str = '',
        template_id: Optional[int] = None,
        kickoff_id: Optional[int] = None,
        task_id: Optional[int] = None,
        fieldset_id: Optional[int] = None,
        dataset=None,
        dataset_id: Optional[int] = None,
        api_name: Optional[str] = None,
        **kwargs,
    ):
        if dataset is not None and dataset_id is None:
            dataset_id = dataset.pk if hasattr(dataset, 'pk') else dataset
        params = {
            'account': self.account,
            'name': name,
            'type': type,
            'order': order,
            'description': description,
            'is_required': is_required,
            'is_hidden': is_hidden,
            'default': default,
            'template_id': template_id,
            'kickoff_id': kickoff_id,
            'task_id': task_id,
            'fieldset_id': fieldset_id,
            'dataset_id': dataset_id,
        }
        if api_name:
            params['api_name'] = api_name
        self.instance = FieldTemplate.objects.create(**params)
        return self.instance

    def _create_related(
        self,
        selections: Optional[list] = None,
        **kwargs,
    ):
        if selections:
            self.create_selections(selections_data=selections)

    def create_selections(self, selections_data: list):
        service = FieldTemplateSelectionService(
            user=self.user,
            is_superuser=self.is_superuser,
            auth_type=self.auth_type,
        )
        for selection_data in selections_data:
            service.create(
                field_template_id=self.instance.id,
                template_id=self.instance.template_id,
                **selection_data,
            )
