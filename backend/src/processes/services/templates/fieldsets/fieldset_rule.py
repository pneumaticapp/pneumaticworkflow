from typing import List, Optional
from django.contrib.auth import get_user_model
from django.db import transaction
from src.generics.base.service import BaseModelService
from src.processes.enums import FieldSetRuleType, FieldType
from src.processes.models.templates.fields import FieldTemplate
from src.processes.models.templates.fieldset import (
    FieldsetTemplateRule,
)
from src.processes.services.exceptions import (
    FieldsetTemplateRuleSumMaxFieldsNotNumber,
    FieldsetTemplateRuleSumMaxInvalidValue,
    FieldsetTemplateRuleServiceException,
)
from src.processes.messages.fieldset import MSG_FS_0005


UserModel = get_user_model()


class FieldsetTemplateRuleService(BaseModelService):

    def _validate_sum_equal(self, **kwargs) -> float:

        value = self.instance.value
        if not value:
            raise FieldsetTemplateRuleSumMaxInvalidValue
        try:
            result = float(value)
        except (ValueError, TypeError) as ex:
            raise FieldsetTemplateRuleSumMaxInvalidValue from ex

        if self.instance.fields.exclude(type=FieldType.NUMBER).exists():
            raise FieldsetTemplateRuleSumMaxFieldsNotNumber
        return result

    def _validate(self, **kwargs):

        """ Call after objects save """

        validator = getattr(self, f'_validate_{self.instance.type}', None)
        validator(**kwargs)

    def _create_instance(
        self,
        type: FieldSetRuleType.LITERALS,  # noqa: A002
        value: Optional[str] = None,
        fieldset_id: Optional[int] = None,
        **kwargs,
    ):
        self.instance = FieldsetTemplateRule.objects.create(
            account=self.account,
            type=type,
            value=value,
            fieldset_id=fieldset_id,
        )
        return self.instance

    def _create_related(
        self,
        **kwargs,
    ):
        fields = kwargs.pop('fields', None)
        if fields is not None:
            self._set_fields(fields)

    def _get_valid_fields(
        self,
        fields_api_names: List[str],
        **kwargs,
    ) -> List[FieldTemplate]:

        rule_type = kwargs.get('type') or self.instance.type
        available_fields = list(
            FieldTemplate.objects
            .filter(
                fieldset_id=self.instance.fieldset_id,
                api_name__in=fields_api_names,
            ),
        )
        fields_api_names = set(fields_api_names)
        available_api_names = {field.api_name for field in available_fields}
        failed_api_names = fields_api_names - available_api_names
        if failed_api_names:
            raise FieldsetTemplateRuleServiceException(
                message=MSG_FS_0005(
                    rule=rule_type,
                    field=failed_api_names.pop(),
                ),
            )
        return available_fields

    def _set_fields(self, fields_api_names: List[str], **kwargs):
        if fields_api_names:
            fields = self._get_valid_fields(fields_api_names, **kwargs)
            self.instance.fields.set(fields)
        else:
            self.instance.fields.clear()

    def create(
        self,
        **kwargs,
    ) -> FieldsetTemplateRule:

        with transaction.atomic():
            self._create_instance(**kwargs)
            self._create_related(**kwargs)
            self._create_actions(**kwargs)
            self._validate(**kwargs)
        return self.instance

    def partial_update(self, **update_kwargs) -> FieldsetTemplateRule:
        fields = update_kwargs.pop('fields', None)
        with transaction.atomic():
            result = super().partial_update(**update_kwargs, force_save=True)
            if fields is not None:
                self._set_fields(fields)
            self._validate(**update_kwargs)
            return result
