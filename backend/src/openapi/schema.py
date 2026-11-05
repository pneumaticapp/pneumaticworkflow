"""Project path parameter types without executing request-bound querysets."""

import re

from drf_spectacular.openapi import AutoSchema
from drf_spectacular.plumbing import (
    ResolvedComponent,
    build_choice_field,
    force_instance,
)
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from rest_framework.fields import ChoiceField, Field, URLField

from src.openapi.workflow_enums import WORKFLOW_EVENT_TYPE_CHOICES
from src.webhooks.enums import HookEvent


class PneumaticAutoSchema(AutoSchema):
    EVENT_TYPE_RESPONSE_SERIALIZERS = frozenset({
        'src.processes.serializers.workflows.events.WorkflowEventSerializer',
        'src.reports.serializers.EventHighlightsSerializer',
    })
    FULL_PATCH_REQUEST_SERIALIZERS = frozenset({
        'src.processes.serializers.templates.preset.TemplatePresetSerializer',
    })
    OPTIONAL_RESPONSE_FIELDS = {
        (
            'src.processes.serializers.templates.field.'
            'FieldTemplateListSerializer'
        ): frozenset({'selections'}),
        (
            'src.processes.serializers.templates.template.'
            'TemplateListSerializer'
        ): frozenset({'workflows_count'}),
    }

    # Response metadata only: retain the original runtime field options.
    NULLABLE_RESPONSE_FIELDS = {
        'src.accounts.serializers.tenant.TenantSerializer': frozenset({
            'tenant_name',
        }),
        'src.accounts.serializers.mixins.VacationSerializer': frozenset({
            'start_date', 'end_date',
        }),
        'src.accounts.serializers.user.UserSerializer': frozenset({
            'vacation',
        }),
        'src.accounts.serializers.user.UserWebsocketSerializer': frozenset({
            'vacation',
        }),
        'src.authentication.serializers.ContextUserSerializer': frozenset({
            'vacation',
        }),
        (
            'src.processes.serializers.workflows.events.'
            'TaskEventJsonSerializer'
        ): frozenset({'output', 'fieldsets', 'sub_workflow'}),
        (
            'src.processes.serializers.workflows.task.'
            'WorkflowCurrentTaskSerializer'
        ): frozenset({'delay'}),
        (
            'src.processes.serializers.workflows.workflow.'
            'WorkflowDetailsSerializer'
        ): frozenset({'kickoff', 'template', 'workflow_starter'}),
        (
            'src.processes.serializers.workflows.workflow.'
            'WorkflowListSerializer'
        ): frozenset({'template', 'workflow_starter'}),
    }

    INTEGER_PATH_PARAMETERS = frozenset(
        {
            'id',
            'pk',
            'user_id',
            'task_id',
            'workflow_id',
            'template_id',
            'field_id',
            'preset_id',
            'tenant_id',
            'group_id',
        },
    )

    def get_override_parameters(self) -> list:
        parameters = super().get_override_parameters()
        explicit = {
            parameter.name
            for parameter in parameters
            if isinstance(parameter, OpenApiParameter)
            and parameter.location == OpenApiParameter.PATH
        }
        for name in re.findall(r'\{([^}]+)\}', self.path):
            if name in explicit:
                continue
            if name in self.INTEGER_PATH_PARAMETERS:
                parameters.append(
                    OpenApiParameter(
                        name,
                        OpenApiTypes.INT,
                        OpenApiParameter.PATH,
                    ),
                )
            elif name == 'event':
                parameters.append(
                    OpenApiParameter(
                        name,
                        OpenApiTypes.STR,
                        OpenApiParameter.PATH,
                        enum=sorted(HookEvent.VALUES),
                    ),
                )
        return parameters

    def _map_serializer_field(
        self, field, direction, bypass_extensions=False,
    ):
        schema = super()._map_serializer_field(
            field, direction, bypass_extensions,
        )
        if (
            schema and direction == 'response' and field.field_name == 'type'
            and any(
                f'{parent.__module__}.{parent.__name__}'
                in self.EVENT_TYPE_RESPONSE_SERIALIZERS
                for parent in type(field.parent).__mro__
            )
        ):
            schema = {
                **schema,
                **build_choice_field(ChoiceField(
                    choices=WORKFLOW_EVENT_TYPE_CHOICES,
                )),
            }
        if (
            schema and direction == 'response'
            and self._is_nullable_response_field(field)
        ):
            schema = {**schema, 'nullable': True}
        if schema and schema.get('nullable') and (
            'allOf' in schema or '$ref' in schema
        ):
            schema = schema.copy()
            alternatives = schema.pop('allOf', [])
            if '$ref' in schema:
                alternatives = [*alternatives, {'$ref': schema.pop('$ref')}]
            schema.pop('nullable')
            schema['anyOf'] = [
                {'allOf': alternatives},
                {'type': 'object', 'nullable': True, 'enum': [None]},
            ]
        return schema

    def _insert_field_validators(self, field: Field, schema: dict) -> None:
        super()._insert_field_validators(field, schema)
        if not (
            isinstance(field, URLField) and field.allow_blank
            and schema.get('type') == 'string'
            and schema.get('format') == 'uri'
        ):
            return

        uri_schema = schema.copy()
        uri_schema['minLength'] = max(1, uri_schema.get('minLength', 0))
        schema.clear()
        for annotation in (
            'title', 'description', 'default', 'example',
            'readOnly', 'writeOnly', 'deprecated', 'externalDocs',
        ):
            if annotation in uri_schema:
                schema[annotation] = uri_schema.pop(annotation)
        schema['oneOf'] = [
            uri_schema,
            {'type': 'string', 'enum': ['']},
        ]

    def _map_serializer(
        self, serializer, direction, bypass_extensions=False,
    ) -> dict:
        serializer = force_instance(serializer)
        schema = super()._map_serializer(
            serializer, direction, bypass_extensions,
        )
        if (
            direction == 'request' and self.method == 'PATCH'
            and any(
                f'{parent.__module__}.{parent.__name__}'
                in self.FULL_PATCH_REQUEST_SERIALIZERS
                for parent in type(serializer).__mro__
            )
        ):
            schema = {**schema, 'required': [
                name for name, field in serializer.fields.items()
                if field.required and not field.read_only
            ]}
        if direction != 'response' or 'required' not in schema:
            return schema
        serializer_class = (
            serializer if isinstance(serializer, type) else type(serializer)
        )
        optional = {
            field for parent in serializer_class.__mro__
            for field in self.OPTIONAL_RESPONSE_FIELDS.get(
                f'{parent.__module__}.{parent.__name__}', (),
            )
        }
        if optional:
            schema = {**schema, 'required': [
                name for name in schema['required'] if name not in optional
            ]}
            if not schema['required']:
                schema.pop('required')
        return schema

    def _is_nullable_response_field(self, field: Field) -> bool:
        return any(
            field.field_name in self.NULLABLE_RESPONSE_FIELDS.get(
                f'{parent.__module__}.{parent.__name__}', (),
            )
            for parent in type(field.parent).__mro__
        )

    def _get_paginator(self):
        action = getattr(self.view, 'action', None)
        action_paginators = getattr(self.view, 'action_paginator_classes', {})
        if action in action_paginators:
            return action_paginators[action]()
        return super()._get_paginator()

    def _get_response_for_code(
        self,
        serializer,
        status_code,
        media_types=None,
        direction='response',
    ) -> dict:
        response = super()._get_response_for_code(
            serializer,
            status_code,
            media_types,
            direction,
        )
        paginator = self._get_paginator()
        if (
            not str(status_code).startswith('2')
            or paginator is None
        ):
            return response
        for media in response.get('content', {}).values():
            paginated = media['schema']
            component = paginated
            ref = paginated.get('$ref')
            if ref:
                component = self.registry[
                    (ref.rsplit('/', 1)[1], ResolvedComponent.SCHEMA)
                ].schema
            results = component.get('properties', {}).get('results')
            if results and results.get('type') == 'array':
                component['required'] = [
                    'count', 'next', 'previous', 'results',
                ]
                if paginator.default_limit is not None:
                    continue
                media['schema'] = {'oneOf': [results.copy(), paginated]}
                response['description'] = (
                    response.get('description', '')
                    + '\nWithout limit: a flat array. '
                    'With a valid positive limit: a paginated envelope.'
                ).strip()
        return response
