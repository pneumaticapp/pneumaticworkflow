from typing import Optional
from django.contrib.auth import get_user_model

from src.generics.base.service import BaseModelService
from src.processes.enums import FieldSetRuleType
from src.processes.models.templates.fieldset import FieldsetTemplateRule

UserModel = get_user_model()


class FieldsetTemplateRuleService(BaseModelService):

    def _create_instance(
        self,
        name: str,
        type: FieldSetRuleType.LITERALS,  # noqa: A002
        value: Optional[str] = None,
    ):
        self.instance = FieldsetTemplateRule.objects.create(
            account=self.account,
            name=name,
            type=type,
            value=value,
        )
        return self.instance
