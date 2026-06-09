# ruff: noqa: PLC0415
from rest_framework.fields import CharField, SerializerMethodField
from rest_framework.serializers import (
    IntegerField,
    ModelSerializer,
)

from src.generics.fields import (
    RelatedApiNameListField, AccountPrimaryKeyRelatedField,
)
from src.generics.mixins.serializers import CustomValidationErrorMixin
from src.processes.models.templates.fieldset import (
    FieldsetTemplate,
    FieldsetTemplateRule,
)
from src.processes.serializers.templates.field import (
    FieldTemplateSerializer,
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


class SharedFieldsetTemplateSerializer(
    CustomValidationErrorMixin,
    ModelSerializer,
):

    class Meta:
        model = FieldsetTemplate
        fields = (
            'id',
            'name',
            'title',
            'description',
            'label_position',
            'api_name',
            'layout',
            'rules',
            'fields',
        )

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


class FieldsetTemplateSerializer(
    ModelSerializer,
):

    class Meta:
        model = FieldsetTemplate
        fields = (
            'name',
            'title',
            'order',
            'description',
            'api_name',
            'shared_fieldset_id',
            'label_position',
            'layout',
            'rules',
            'fields',
        )

    shared_fieldset_id = AccountPrimaryKeyRelatedField(
        queryset=FieldsetTemplate.objects.all(),
        required=True,
    )
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
