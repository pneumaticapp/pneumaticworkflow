from src.ai.performers.output_fields import (
    OutputField,
    find_blocking_fields,
    is_fillable,
    resolve_output_fields,
)
from src.ai.tests.performers.fixtures import TASK_OUTPUT


def _field(field_type, selections=(), is_required=False):
    return OutputField(
        api_name='x',
        name='X',
        type=field_type,
        is_required=is_required,
        selections=tuple(selections),
    )


def test_resolve__hidden_field__excluded():
    fields = resolve_output_fields(TASK_OUTPUT)

    assert not any(f.api_name == 'f-hidden' for f in fields)


def test_resolve__choice_field__selections_are_display_values():
    fields = resolve_output_fields(TASK_OUTPUT)

    radio = next(f for f in fields if f.api_name == 'f-radio')
    assert radio.selections == ('Yes', 'No')


def test_find_blocking_fields__normal_task__empty():
    fields = resolve_output_fields(TASK_OUTPUT)

    assert find_blocking_fields(fields) == []


def test_is_fillable__file_field__true():
    # File fields are fillable via generated documents.
    assert is_fillable(_field('file')) is True


def test_is_fillable__user_field__false():
    assert is_fillable(_field('user')) is False


def test_is_fillable__choice_without_selections__false():
    assert is_fillable(_field('dropdown')) is False


def test_find_blocking_fields__required_unfillable__blocks():
    task_output = [
        {
            'api_name': 'f-file', 'name': 'Artifact', 'type': 'file',
            'is_required': True, 'is_hidden': False, 'selections': [],
        },
        {
            'api_name': 'f-user', 'name': 'Owner', 'type': 'user',
            'is_required': True, 'is_hidden': False, 'selections': [],
        },
        {
            'api_name': 'f-empty', 'name': 'Empty', 'type': 'dropdown',
            'is_required': True, 'is_hidden': False, 'selections': [],
        },
    ]

    blocking = find_blocking_fields(resolve_output_fields(task_output))

    assert sorted(f.api_name for f in blocking) == ['f-empty', 'f-user']
