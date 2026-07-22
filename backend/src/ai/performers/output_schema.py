import json
from typing import (
    Dict,
    List,
    Union,
)

from src.ai.performers.output_fields import (
    STRING_MAX_LENGTH,
    OutputField,
    is_choice_type,
)
from src.processes.enums import FieldType

# Pneumatic renders text field values as Markdown, where single newlines
# collapse into one paragraph — a model writing "one item per line"
# comes out as a run-on blob unless it uses Markdown structure.
MARKDOWN_NOTE = (
    'Rendered as Markdown: single newlines collapse, so format lists as '
    'Markdown lists ("- item") and separate paragraphs with blank lines.'
)


class UnsupportedFieldTypeError(Exception):
    pass


def _nullable(json_type: str, is_required: bool) -> Union[str, List[str]]:
    # Optional fields must still appear in a strict schema, so they are
    # made nullable instead.
    return json_type if is_required else [json_type, 'null']


def _describe(field: OutputField) -> str:
    parts = [field.name]
    if field.description:
        parts.append(field.description)
    if not field.is_required:
        parts.append(
            'Optional — return null if the task gives you nothing '
            'to put here.',
        )
    return '. '.join(parts)


def _property_for(field: OutputField) -> Dict:
    description = _describe(field)

    if field.type == FieldType.STRING:
        # Strict-mode providers reject constraint keywords like
        # `maxLength`, so the limit lives in the description and is
        # enforced on the way out.
        return {
            'type': _nullable('string', field.is_required),
            'description': (
                f'{description} At most {STRING_MAX_LENGTH} characters.'
            ),
        }
    if field.type == FieldType.TEXT:
        return {
            'type': _nullable('string', field.is_required),
            'description': f'{description} {MARKDOWN_NOTE}',
        }
    if field.type == FieldType.URL:
        return {
            'type': _nullable('string', field.is_required),
            'description': (
                f'{description} Must be an absolute URL including '
                f'the scheme.'
            ),
        }
    if field.type == FieldType.DATE:
        return {
            'type': _nullable('string', field.is_required),
            'description': (
                f'{description} Format as an ISO 8601 date, '
                f'e.g. 2026-07-10.'
            ),
        }
    if field.type == FieldType.NUMBER:
        return {
            'type': _nullable('number', field.is_required),
            'description': description,
        }
    if field.type in FieldType.TYPES_WITH_SELECTION:
        selections = list(field.selections)
        if field.is_required:
            return {
                'description': description,
                'type': 'string',
                'enum': selections,
            }
        # A mixed-type enum ([...values, null]) trips some strict-mode
        # validators; a property-level anyOf is the supported spelling.
        return {
            'description': description,
            'anyOf': [
                {'type': 'string', 'enum': selections},
                {'type': 'null'},
            ],
        }
    if field.type == FieldType.CHECKBOX:
        return {
            'description': description,
            'type': _nullable('array', field.is_required),
            'items': {'type': 'string', 'enum': list(field.selections)},
        }
    if field.type == FieldType.FILE:
        # The model writes the document; the pipeline uploads it and
        # turns it into the link Pneumatic expects.
        document = {
            'type': 'object',
            'properties': {
                'filename': {
                    'type': 'string',
                    'description': (
                        'Name for the generated file, ending in .md'
                    ),
                },
                'content': {
                    'type': 'string',
                    'description': (
                        'The complete document, written in Markdown.'
                    ),
                },
            },
            'required': ['filename', 'content'],
            'additionalProperties': False,
        }
        description = f'{description} Write the document this field asks for.'
        if field.is_required:
            document['description'] = description
            return document
        return {
            'description': description,
            'anyOf': [document, {'type': 'null'}],
        }
    raise UnsupportedFieldTypeError(
        f'build_output_schema: unsupported field type "{field.type}"',
    )


def build_output_schema(fields: List[OutputField]) -> Dict:

    """Builds a JSON Schema keyed by field api_name, so the model's
    response maps straight onto Pneumatic's output object. Choice enums
    are the display values — which is also what task completion expects
    on the wire."""

    return {
        'type': 'object',
        'properties': {
            field.api_name: _property_for(field) for field in fields
        },
        # Strict mode requires every property to be listed,
        # nullable or not.
        'required': [field.api_name for field in fields],
        'additionalProperties': False,
    }


def describe_fields(fields: List[OutputField]) -> str:

    """Renders the schema as prose for models that can't be constrained
    by it, and to give the model the field semantics that opaque
    api_name keys hide."""

    blocks = []
    for field in fields:
        requiredness = 'required' if field.is_required else 'optional'
        bits = [
            f'- "{field.api_name}" ({field.type}, {requiredness}): '
            f'{field.name}',
        ]
        if field.description:
            bits.append(f'  {field.description}')
        if is_choice_type(field.type):
            values = ', '.join(
                json.dumps(selection) for selection in field.selections
            )
            if field.type == FieldType.CHECKBOX:
                rule = 'Any number of'
            elif field.is_required:
                rule = 'Exactly one of'
            else:
                rule = 'One of (or null)'
            bits.append(f'  {rule}: {values}')
        if field.type == FieldType.TEXT:
            bits.append(f'  {MARKDOWN_NOTE}')
        if field.type == FieldType.FILE:
            bits.append(
                '  Write a Markdown document: {"filename": "<name>.md", '
                '"content": "<the full document>"}',
            )
        blocks.append('\n'.join(bits))
    return '\n'.join(blocks)
