from typing import (
    Dict,
    List,
    NamedTuple,
    Tuple,
)

from src.processes.enums import FieldType

# Field types a language model can produce a value for.
# FieldType.FILE is filled by generating a markdown document, uploading
# it to the file service and completing with the returned link.
# FieldType.USER needs a real Pneumatic user id, so it stays unfillable.
FILLABLE_TYPES = frozenset({
    FieldType.STRING,
    FieldType.TEXT,
    FieldType.URL,
    FieldType.DATE,
    FieldType.NUMBER,
    FieldType.RADIO,
    FieldType.DROPDOWN,
    FieldType.CHECKBOX,
    FieldType.FILE,
})

CHOICE_TYPES = frozenset(FieldType.TYPES_WITH_SELECTIONS)

# Pneumatic 'string' fields error past 140 characters; 'text' is
# unbounded.
STRING_MAX_LENGTH = 140


class OutputField(NamedTuple):
    api_name: str
    name: str
    type: str
    is_required: bool
    description: str = ''
    selections: Tuple[str, ...] = ()


def is_choice_type(field_type: str) -> bool:
    return field_type in CHOICE_TYPES


def resolve_output_fields(task_output: List[Dict]) -> List[OutputField]:

    """Normalizes a task's output-field descriptions.

    Accepts dicts shaped like the v2 task API renders them — the runtime
    truth: it knows which fields the workflow's conditions have hidden
    (``is_hidden``) and carries choice ``selections`` as display-value
    strings, which is exactly what task completion expects back
    (selection api_names are a template-editing concept and never appear
    on the completion wire)."""

    fields = []
    for field in task_output:
        if field.get('is_hidden'):
            continue
        field_type = field['type']
        if is_choice_type(field_type):
            selections = tuple(field.get('selections') or ())
        else:
            selections = ()
        fields.append(
            OutputField(
                api_name=field['api_name'],
                name=field['name'],
                description=field.get('description') or '',
                type=field_type,
                is_required=bool(field.get('is_required')),
                selections=selections,
            ),
        )
    return fields


def is_fillable(field: OutputField) -> bool:

    """A choice field with no selections offers the model nothing
    to pick from."""

    return (
        field.type in FILLABLE_TYPES
        and not (is_choice_type(field.type) and not field.selections)
    )


def find_blocking_fields(fields: List[OutputField]) -> List[OutputField]:

    """Required fields we cannot fill block the whole task: completion
    rejects a submission that omits them, so there is no point calling
    the model at all."""

    return [
        field for field in fields
        if field.is_required and not is_fillable(field)
    ]
