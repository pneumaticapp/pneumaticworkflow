from rest_framework.fields import CharField
from rest_framework.serializers import (
    IntegerField,
    ModelSerializer,
)

from src.generics.fields import (
    RelatedApiNameField,
    RelatedApiNameListField,
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
            'type',
            'value',
            'api_name',
            'fields',
        )

    api_name = CharField(required=False, max_length=200)
    fields = RelatedApiNameListField(
        required=False,
        allow_empty=True,
        default=list,
    )


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
            'task',
            'label_position',
            'layout',
            'rules',
            'fields',
            'api_name',
        )

    id = IntegerField(required=False)
    task = RelatedApiNameField(
        queryset=TaskTemplate.objects.all(),
        required=False,
        allow_null=True,
    )
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
        if 'task' in attrs and attrs['task'] is not None:
            task = attrs.pop('task')
            attrs['task_id'] = task.id
        return attrs
