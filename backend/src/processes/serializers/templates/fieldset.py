from django.core.validators import MinValueValidator
from rest_framework.fields import CharField, ChoiceField, IntegerField
from rest_framework.serializers import ModelSerializer
from src.generics.fields import (
    AccountPrimaryKeyRelatedField,
)
from src.generics.mixins.serializers import CustomValidationErrorMixin
from src.processes.enums import FieldSetLayout, LabelPosition
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

    shared_fieldset_id = AccountPrimaryKeyRelatedField(
        queryset=FieldsetTemplate.objects.shared(),
        required=True,
    )
    api_name = CharField(required=False, max_length=200)
    name = CharField(required=False, max_length=1000)
    label_position = ChoiceField(
        choices=LabelPosition.CHOICES,
        required=False,
    )
    layout = ChoiceField(
        choices=FieldSetLayout.CHOICES,
        required=False,
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
    order = IntegerField(
        required=False,
        default=0,
        validators=[MinValueValidator(0)],
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
