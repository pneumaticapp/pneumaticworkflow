"""OpenApiSerializerFieldExtension for Doc* serializer fields."""

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
