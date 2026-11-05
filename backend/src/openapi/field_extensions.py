"""OpenApiSerializerFieldExtension for Doc* serializer fields."""

from django.core.exceptions import FieldDoesNotExist

from drf_spectacular.extensions import OpenApiSerializerFieldExtension


class DocExampleFieldExtension(OpenApiSerializerFieldExtension):
    target_class = 'src.generics.fields.DocExampleMixin'
    match_subclasses = True

    def map_serializer_field(self, auto_schema, direction):
        schema = auto_schema._map_serializer_field(
            self.target,
            direction,
            bypass_extensions=True,
        )
        if schema is None:
            return None
        example = getattr(self.target, 'example', None)
        if example is None:
            return schema
        schema = dict(schema)
        schema['example'] = example
        return schema


class TemplateDraftBooleanFieldExtension(OpenApiSerializerFieldExtension):
    target_class = (
        'src.openapi.template_serializers.TemplateDraftBooleanField'
    )

    def map_serializer_field(
        self, auto_schema: object, direction: str,
    ) -> dict:
        return {'type': 'boolean'} if direction == 'response' else {}


class TimeStampFieldExtension(OpenApiSerializerFieldExtension):
    target_class = 'src.generics.fields.TimeStampField'
    match_subclasses = True
    priority = 1

    def map_serializer_field(self, auto_schema, direction):
        number = {'type': 'number', 'format': 'double'}
        schema = {
            **number,
            'description': 'Unix timestamp in seconds, not ISO date-time.',
            'example': 1767225600.0,
        }
        if direction == 'request':
            schema.pop('type')
            schema.pop('format')
            if self.target.allow_null:
                number['nullable'] = True
            schema['oneOf'] = [
                number,
                {
                    'type': 'string',
                    'pattern': (
                        r'^\s*[+-]?(?:\d+(?:\.\d*)?|\.\d+)'
                        r'(?:[eE][+-]?\d+)?\s*$'
                    ),
                    'description': 'Numeric timestamp.',
                },
            ]
        elif self._is_nullable_model_field():
            schema['nullable'] = True
        return schema

    def _is_nullable_model_field(self) -> bool:
        field = self.target
        model = getattr(getattr(field.parent, 'Meta', None), 'model', None)
        if model is None:
            return field.allow_null
        source = field.source_attrs or [field.field_name]
        try:
            return model._meta.get_field(source[0]).null
        except FieldDoesNotExist:
            return field.allow_null
