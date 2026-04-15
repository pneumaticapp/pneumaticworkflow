from django.utils.translation import ugettext_lazy as _

from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField
from rest_framework.serializers import (
    IntegerField,
    ModelSerializer,
)

from src.generics.mixins.serializers import CustomValidationErrorMixin
from src.processes.models.templates.fieldset import (
    FieldsetTemplate,
    FieldsetTemplateRule,
)
from src.processes.models.templates.task import TaskTemplate
from src.processes.serializers.templates.field import FieldTemplateSerializer


class FieldsetTemplateRuleSerializer(
    CustomValidationErrorMixin,
    ModelSerializer,
):

    class Meta:
        model = FieldsetTemplateRule
        fields = (
            'id',
            'type',
            'value',
            'api_name',
        )

    id = IntegerField(read_only=True)
    api_name = CharField(required=False, max_length=200)


class FieldsetTemplateSerializer(
    CustomValidationErrorMixin,
    ModelSerializer,
):

    class Meta:
        model = FieldsetTemplate
        fields = (
            'id',
            'name',
            'description',
            'order',
            'task_id',
            'label_position',
            'layout',
            'rules',
            'fields',
            'api_name',
        )

    id = IntegerField(read_only=True)
    task_id = IntegerField(allow_null=True, required=False)
    api_name = CharField(required=False, max_length=200)
    rules = FieldsetTemplateRuleSerializer(
        many=True,
        required=False,
        default=list,
    )
    fields = FieldTemplateSerializer(
        many=True,
        required=False,
        default=list,
    )

    def validate(self, attrs):

        if self.instance:
            account = self.instance.account
            template = self.instance.template
        else:
            account = self.context.get('account')
            template = self.context.get('template')

        task_id = attrs.get('task_id')

        if task_id:
            if task_id is None:
                attrs['kickoff_id'] = template.kickoff_instance.id
            else:
                attrs['kickoff_id'] = None
                if not TaskTemplate.objects.filter(
                    pk=task_id,
                    template_id=template.id,
                    account_id=account.id,
                ).exists():
                    raise ValidationError(
                        {'task_id': _('Invalid task_id for this fieldset.')},
                    )
        return attrs
