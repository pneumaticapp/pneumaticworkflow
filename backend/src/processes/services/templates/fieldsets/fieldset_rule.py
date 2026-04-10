from typing import Optional
from django.contrib.auth import get_user_model
from django.db.models import Model

from src.generics.base.service import BaseModelService
from src.processes.enums import FieldSetRuleType, FieldType
from src.processes.models.templates.fields import FieldTemplate
from src.processes.models.templates.fieldset import (
    FieldsetTemplateRule,
)
from src.processes.services.exceptions import (
    FieldsetTemplateRuleSumMaxFieldsNotNumber,
    FieldsetTemplateRuleSumMaxInvalidValue,
)

UserModel = get_user_model()


class FieldsetTemplateRuleService(BaseModelService):

    def create(self, **kwargs) -> Model:
        self._validate(**kwargs)
        return super().create(**kwargs)

    def partial_update(self, **update_kwargs) -> Model:
        self._validate(**update_kwargs)
        return super().partial_update(**update_kwargs)

    def _validate(self, **kwargs):
        rule_type = kwargs.get('type') or (
            self.instance.type if self.instance else None
        )
        validator = getattr(self, f'_validate_{rule_type}', None)
        validator(**kwargs)

    def _validate_sum_max(self, **kwargs):
        value = kwargs.get('value') if 'value' in kwargs else (
            self.instance.value if self.instance else None
        )
        if not value:
            raise FieldsetTemplateRuleSumMaxInvalidValue
        try:
            float(value)
        except (ValueError, TypeError) as ex:
            raise FieldsetTemplateRuleSumMaxInvalidValue from ex

        fieldset_id = kwargs.get('fieldset_id') or (
            self.instance.fieldset_id if self.instance else None
        )
        non_number_exists = (
            FieldTemplate.objects
            .filter(fieldset_id=fieldset_id)
            .exclude(type=FieldType.NUMBER)
            .exists()
        )
        if non_number_exists:
            raise FieldsetTemplateRuleSumMaxFieldsNotNumber

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
