from rest_framework.fields import CharField, SerializerMethodField
from rest_framework.serializers import (
    IntegerField,
    ModelSerializer,
)

from src.generics.fields import (
    RelatedApiNameListField,
)
from src.generics.mixins.serializers import CustomValidationErrorMixin
from src.processes.models.templates.fieldset import (
    FieldsetTemplate,
    FieldsetTemplateRule,
)
from src.processes.serializers.templates.field import FieldTemplateSerializer
from src.processes.serializers.templates.task import (
    TemplateStepNameSerializer,
)


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
            'label_position',
            'layout',
            'rules',
            'fields',
            'api_name',
            'tasks',
            'kickoff',
        )

    id = IntegerField(required=False)
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
    tasks = TemplateStepNameSerializer(
        many=True,
        read_only=True,
        default=list,
    )
    kickoff = SerializerMethodField()

    def get_kickoff(self, instance: FieldsetTemplate):
        kickoff = instance.kickoffs.all().first()
        return kickoff.id if kickoff else None
