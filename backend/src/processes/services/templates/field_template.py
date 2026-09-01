from typing import Optional, List, Dict
from django.db import IntegrityError, transaction
from django.db.models import Model

from src.generics.base.service import BaseModelService
from src.processes.enums import FieldType
from src.processes.messages.fieldset import MSG_FS_0015, MSG_FS_0016
from src.processes.models.templates.fields import (
    FieldTemplate,
    FieldTemplateRuleSet,
)
from src.processes.models.templates.fieldset import FieldsetTemplate
from src.processes.services.exceptions import (
    FieldTemplateSelectionsRequired,
    FieldTemplateUserMustBeRequired, FieldTemplateServiceException,
    FieldTemplateRuleSetServiceException,
)
from src.processes.services.templates.field_template_rule import (
    FieldTemplateRuleSetService,
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

    def _get_step_name(self, fieldset_id: Optional[int] = None) -> str:
        fieldset = None
        if fieldset_id:
            fieldset = FieldsetTemplate.objects.filter(id=fieldset_id).first()
        elif self.instance and self.instance.fieldset_id:
            fieldset = self.instance.fieldset
        if not fieldset:
            return 'Kickoff'
        if fieldset.kickoff_id:
            return 'Kickoff'
        if fieldset.task_id:
            return fieldset.task.name
        return 'Kickoff'

    def create(self, **kwargs) -> Model:
        self._validate(**kwargs)
        return super().create(**kwargs)

    def partial_update(self, **update_kwargs) -> Model:
        self._validate(**update_kwargs)
        selections_data = update_kwargs.pop('selections', None)
        rulesets_data = update_kwargs.pop('rulesets', None)
        result = super().partial_update(**update_kwargs)
        if selections_data is not None:
            self.instance.selections.all().delete()
            self.create_selections(selections_data=selections_data)
        if rulesets_data is not None:
            self.update_rulesets(rulesets_data=rulesets_data)
        return result

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
        step_name = self._get_step_name(fieldset_id=fieldset_id)
        try:
            with transaction.atomic():
                self.instance = FieldTemplate.objects.create(**params)
        except IntegrityError as ex:
            raise FieldTemplateServiceException(
                message=MSG_FS_0015(
                    name=step_name,
                    field_name=name,
                    api_name=api_name,
                ),
            ) from ex
        return self.instance

    def _create_related(
        self,
        selections: Optional[list] = None,
        rulesets: Optional[List[Dict]] = None,
        **kwargs,
    ):
        if selections:
            self.create_selections(selections_data=selections)
        if rulesets:
            self.create_rulesets(rulesets_data=rulesets)

    def create_selections(self, selections_data: list):
        service = FieldTemplateSelectionService(
            user=self.user,
            is_superuser=self.is_superuser,
            auth_type=self.auth_type,
        )
        step_name = self._get_step_name()
        for selection_data in selections_data:
            try:
                service.create(
                    field_template_id=self.instance.id,
                    template_id=self.instance.template_id,
                    **selection_data,
                )
            except IntegrityError as ex:
                raise FieldTemplateServiceException(
                    message=MSG_FS_0016(
                        name=step_name,
                        api_name=selection_data.get('api_name'),
                    ),
                ) from ex

    def create_ruleset(
        self,
        ruleset_data: dict,
    ) -> FieldTemplateRuleSet:

        service = FieldTemplateRuleSetService(
            user=self.user,
            is_superuser=self.is_superuser,
            auth_type=self.auth_type,
        )
        try:
            return service.create(
                field_id=self.instance.id,
                template_id=self.instance.template_id,
                **ruleset_data,
            )
        except FieldTemplateRuleSetServiceException as ex:
            raise FieldTemplateServiceException(message=ex.message) from ex

    def create_rulesets(
        self,
        rulesets_data: List[Dict],
    ):
        for ruleset_data in rulesets_data:
            self.create_ruleset(ruleset_data)

    def update_rulesets(
        self,
        rulesets_data: List[Dict],
    ):
        """ All rulesets will be updated """

        existing_rulesets = {
            ruleset.api_name: ruleset
            for ruleset in self.instance.rulesets.all()
        }
        ruleset_api_names = set()
        for ruleset_data in rulesets_data:
            ruleset_data_dict = dict(ruleset_data)
            ruleset_api_name = ruleset_data_dict.get('api_name')
            if ruleset_api_name and ruleset_api_name in existing_rulesets:
                service = FieldTemplateRuleSetService(
                    user=self.user,
                    is_superuser=self.is_superuser,
                    auth_type=self.auth_type,
                    instance=existing_rulesets[ruleset_api_name],
                )
                service.partial_update(**ruleset_data)
                ruleset_api_names.add(ruleset_api_name)
            else:
                ruleset = self.create_ruleset(ruleset_data)
                ruleset_api_names.add(ruleset.api_name)

        self.instance.rulesets.exclude(
            api_name__in=ruleset_api_names,
        ).delete()
