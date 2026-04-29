from rest_framework.fields import CharField
from rest_framework.serializers import (
    ModelSerializer,
)
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
