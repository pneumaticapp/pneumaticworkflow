from rest_framework.fields import CharField
from rest_framework.serializers import (
    ModelSerializer,
)
from src.processes.serializers.templates.field import FieldTemplateSerializer
from src.generics.mixins.serializers import CustomValidationErrorMixin
from src.processes.models.templates.fieldset import (
    FieldsetTemplateTaskTemplate,
    FieldsetTemplateKickoff,
)


class FieldsetTemplateTaskTemplateSerializer(
    CustomValidationErrorMixin,
    ModelSerializer,
):
    class Meta:
        model = FieldsetTemplateTaskTemplate
        fields = (
            'order',
            'api_name',
        )

    api_name = CharField(source='fieldset.api_name')


class FieldsetTemplateKickoffSerializer(
    CustomValidationErrorMixin,
    ModelSerializer,
):
    class Meta:
        model = FieldsetTemplateKickoff
        fields = (
            'order',
            'api_name',
        )

    api_name = CharField(source='fieldset.api_name')


class FieldsetTemplateKickoffListSerializer(ModelSerializer):
    class Meta:
        model = FieldsetTemplateKickoff
        fields = (
            'order',
            'name',
            'description',
            'fields',
            'api_name',
            'label_position',
            'layout',
        )

    name = CharField(source='fieldset.name')
    description = CharField(source='fieldset.description')
    api_name = CharField(source='fieldset.api_name')
    label_position = CharField(
        source='fieldset.label_position',
    )
    layout = CharField(source='fieldset.layout')
    fields = FieldTemplateSerializer(
        source='fieldset.fields',
        many=True,
    )


class FieldsetTemplateTaskListSerializer(ModelSerializer):

    class Meta:
        model = FieldsetTemplateTaskTemplate
        fields = (
            'order',
            'name',
            'description',
            'fields',
            'api_name',
            'label_position',
            'layout',
        )

    name = CharField(source='fieldset.name')
    description = CharField(source='fieldset.description')
    api_name = CharField(source='fieldset.api_name')
    label_position = CharField(
        source='fieldset.label_position',
    )
    layout = CharField(source='fieldset.layout')
    fields = FieldTemplateSerializer(
        source='fieldset.fields',
        many=True,
    )
