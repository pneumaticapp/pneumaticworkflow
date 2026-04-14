from django.contrib.auth import get_user_model
from src.processes.messages.fieldset import MSG_FS_0002
from src.processes.models.workflows.fieldset import FieldSetRule, FieldSet
from src.processes.services.base import BaseModelService
from src.processes.services.exceptions import FieldsetServiceException


UserModel = get_user_model()


class FieldSetRuleService(BaseModelService):

    NULL_VALUES = (None, '', [])

    def create(self, **kwargs) -> FieldSetRule:
        if kwargs.get('skip_validation') is False:
            self.validate(**kwargs)
        return super().create(**kwargs)

    def partial_update(self, **update_kwargs) -> FieldSetRule:
        self.validate(**update_kwargs)
        return super().partial_update(**update_kwargs)

    def validate(self, **kwargs):
        rule_type = kwargs.get('type') or (
            self.instance.type if self.instance else None
        )
        fieldset = kwargs.get('fieldset') or (
            self.instance.fieldset if self.instance else None
        )
        value = kwargs.get('value') or (
            self.instance.value if self.instance else None
        )
        validator = getattr(self, f'_validate_{rule_type}')
        validator(fieldset=fieldset, value=value)

    def _validate_sum_equal(self, fieldset: FieldSet, value: str):

        total = 0
        for field in fieldset.fields.all():
            if field.value not in self.NULL_VALUES:
                total += float(field.value)
        if total != float(value):
            raise FieldsetServiceException(MSG_FS_0002(value))
        return True

    def _create_instance(self, instance_template, **kwargs):
        self.instance = FieldSetRule.objects.create(
            account=self.account,
            fieldset=kwargs['fieldset'],
            api_name=instance_template.api_name,
            type=instance_template.type,
            value=instance_template.value,
        )
