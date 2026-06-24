from rest_framework.fields import CharField
from rest_framework.serializers import ModelSerializer
from src.generics.fields import (
    AccountPrimaryKeyRelatedField,
)
from src.generics.mixins.serializers import CustomValidationErrorMixin
from src.processes.models.templates.fieldset import (
    FieldsetTemplate,
)
from src.processes.serializers.templates.field import (
    FieldTemplateSerializer,
)
from src.processes.serializers.templates.fieldset_rule import (
    FieldSetTemplateRuleSetSerializer,
)


class FieldsetTemplateSerializer(
    ModelSerializer,
    CustomValidationErrorMixin,
):

    class Meta:
        model = FieldsetTemplate
        fields = (
            'title',
            'order',
            'description',
            'api_name',
            'shared_fieldset_id',
            'name',
            'label_position',
            'layout',
            'rules',
            'fields',
        )

        read_only_fields = (
            'name',
            'label_position',
            'layout',
            'rules',
            'fields',
        )

    shared_fieldset_id = AccountPrimaryKeyRelatedField(
        queryset=FieldsetTemplate.objects.all(),
        required=True,
    )
    api_name = CharField(required=False, max_length=200)
    rules = FieldSetTemplateRuleSetSerializer(
        many=True,
        required=False,
        default=list,
        source='rulesets',
    )
    fields = FieldTemplateSerializer(
        many=True,
        required=False,
        default=list,
    )


class SharedFieldsetTemplateSerializer(
    CustomValidationErrorMixin,
    ModelSerializer,
):

    class Meta:
        model = FieldsetTemplate
        fields = (
            'id',
            'title',
            'order',
            'description',
            'api_name',
            'name',
            'label_position',
            'layout',
            'rules',
            'fields',
        )

    rules = FieldSetTemplateRuleSetSerializer(
        many=True,
        required=False,
        default=list,
        source='rulesets',
    )
    fields = FieldTemplateSerializer(
        many=True,
        required=False,
        default=list,
    )
    api_name = CharField(required=False, max_length=200)
