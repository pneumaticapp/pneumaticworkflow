"""Transport contracts for template import and service projections."""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from src.processes.serializers.templates.condition import (
    ConditionTemplateSerializer,
)
from src.processes.serializers.templates.task import ShortTaskSerializer
from src.processes.serializers.templates.system_template import (
    LibraryTemplateImportSerializer,
    LibraryTemplatesImportRequestSerializer,
)
from src.processes.serializers.templates.template import (
    TemplateByStepsSerializer,
)

STEP_NAME_SCHEMA = {'type': 'string', 'minLength': 1, 'maxLength': 280}
STEP_DESCRIPTION_SCHEMA = {'type': 'string', 'minLength': 1}
STEP_DUE_IN_SCHEMA = {
    'type': 'object',
    'properties': {
        name: {'type': 'integer', 'minimum': 0}
        for name in ('days', 'hours', 'minutes')
    },
    'required': ['days', 'hours', 'minutes'],
}


@extend_schema_field({
    'type': 'object',
    'description': (
        'The import parser accepts camelCase and snake_case field names. '
        'A step name and description are required with either spelling.'
    ),
    'properties': {
        'step_name': STEP_NAME_SCHEMA,
        'stepName': STEP_NAME_SCHEMA,
        'step_description': STEP_DESCRIPTION_SCHEMA,
        'stepDescription': STEP_DESCRIPTION_SCHEMA,
        'due_in': STEP_DUE_IN_SCHEMA,
        'dueIn': STEP_DUE_IN_SCHEMA,
    },
    'allOf': [
        {'anyOf': [{'required': [name]} for name in aliases]}
        for aliases in (
            ('step_name', 'stepName'),
            ('step_description', 'stepDescription'),
        )
    ],
})
class LibraryImportStepField(serializers.JSONField):
    """Raw HTTP spelling before ImportSystemTemplateParser normalizes keys."""


class LibraryTemplateTransportSerializer(LibraryTemplateImportSerializer):
    steps = serializers.ListField(
        child=LibraryImportStepField(), min_length=1,
    )


class LibraryTemplatesImportBodySerializer(
    LibraryTemplatesImportRequestSerializer,
):
    templates = LibraryTemplateTransportSerializer(
        many=True, allow_empty=False,
    )


class GeneratedTemplateStepSerializer(ShortTaskSerializer):
    api_name = serializers.CharField(max_length=200)
    conditions = ConditionTemplateSerializer(many=True)


class GeneratedTemplateStepsSerializer(TemplateByStepsSerializer):
    tasks = GeneratedTemplateStepSerializer(many=True)


class TemplateIntegrationsResponseSerializer(serializers.Serializer):
    """Public service projection omits internal last-activation timestamps."""

    id = serializers.IntegerField()
    shared = serializers.BooleanField()
    api = serializers.BooleanField()
    zapier = serializers.BooleanField()
    webhooks = serializers.BooleanField()
