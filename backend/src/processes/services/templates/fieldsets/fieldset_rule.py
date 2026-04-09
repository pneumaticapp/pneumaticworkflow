from typing import Optional
from django.contrib.auth import get_user_model

from src.generics.base.service import BaseModelService
from src.processes.enums import FieldSetRuleType
from src.processes.models.templates.fieldset import FieldsetTemplateRule

UserModel = get_user_model()


class FieldsetTemplateRuleService(BaseModelService):

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
