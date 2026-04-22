from django.contrib.auth import get_user_model
from django.db import transaction
from src.processes.messages.fieldset import MSG_FS_0002
from src.processes.models.workflows.fieldset import FieldSetRule
from src.processes.services.base import BaseModelService
from src.processes.services.exceptions import FieldsetServiceException


UserModel = get_user_model()


class FieldSetRuleService(BaseModelService):

    NULL_VALUES = (None, '', [])

    def _validate_sum_equal(self, **kwargs):

        total = 0
        for field in self.instance.fields.all():
            if field.value not in self.NULL_VALUES:
                total += float(field.value)
        if total != float(self.instance.value):
            raise FieldsetServiceException(MSG_FS_0002(self.instance.value))
        return True

    def validate(self, **kwargs):

        """ Call after objects save """

        validator = getattr(self, f'_validate_{self.instance.type}')
        validator(**kwargs)

    def _create_instance(self, instance_template, **kwargs):
        self.instance = FieldSetRule.objects.create(
            account=self.account,
            fieldset=kwargs['fieldset'],
            api_name=instance_template.api_name,
            type=instance_template.type,
            value=instance_template.value,
        )

    def create(self, **kwargs) -> FieldSetRule:
        with transaction.atomic():
            self._create_instance(**kwargs)
            self._create_related(**kwargs)
            self._create_actions(**kwargs)
            if kwargs.get('skip_validation') is False:
                self.validate(**kwargs)
        return self.instance

    def partial_update(self, **update_kwargs) -> FieldSetRule:
        with transaction.atomic():
            result = super().partial_update(**update_kwargs)
            self.validate(**update_kwargs)
        return result
