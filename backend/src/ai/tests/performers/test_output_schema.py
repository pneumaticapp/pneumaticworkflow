import pytest

from src.ai.performers.output_fields import OutputField
from src.ai.performers.output_schema import (
    UnsupportedFieldTypeError,
    build_output_schema,
    describe_fields,
)
from src.ai.tests.performers.fixtures import fillable_fields

FIELDS = fillable_fields()
SCHEMA = build_output_schema(FIELDS)


def test_schema__strict_mode__all_properties_required_no_extras():
    assert sorted(SCHEMA['required']) == sorted(SCHEMA['properties'])
    assert len(SCHEMA['required']) == len(FIELDS)
    assert SCHEMA['additionalProperties'] is False


def test_schema__optional_field__nullable_required_not():
    assert SCHEMA['properties']['f-text']['type'] == ['string', 'null']
    assert SCHEMA['properties']['f-str']['type'] == 'string'


def test_schema__text_field__warns_about_markdown_rendering():
    assert 'Rendered as Markdown' in (
        SCHEMA['properties']['f-text']['description']
    )
    assert 'Rendered as Markdown' in describe_fields(FIELDS)


def test_schema__string_field__no_constraint_keywords():
    # `maxLength` & co. 400 on some strict-mode providers; the limit
    # lives in the description.
    assert 'maxLength' not in SCHEMA['properties']['f-str']
    assert '140 characters' in SCHEMA['properties']['f-str']['description']


def test_schema__required_radio__plain_string_enum_of_display_values():
    assert SCHEMA['properties']['f-radio'] == {
        'description': 'Ready?',
        'type': 'string',
        'enum': ['Yes', 'No'],
    }


def test_schema__optional_radio__anyof_not_mixed_type_enum():
    prop = SCHEMA['properties']['f-opt-radio']

    assert 'enum' not in prop
    assert prop['anyOf'] == [
        {'type': 'string', 'enum': ['Good', 'Bad']},
        {'type': 'null'},
    ]


def test_schema__optional_checkbox__nullable_array_with_item_enum():
    prop = SCHEMA['properties']['f-check']

    assert prop['type'] == ['array', 'null']
    assert prop['items'] == {
        'type': 'string',
        'enum': ['Skip review', 'Notify'],
    }


def test_schema__unknown_field_type__raises():
    field = OutputField(
        api_name='x', name='X', type='user', is_required=False,
    )

    with pytest.raises(UnsupportedFieldTypeError):
        build_output_schema([field])


def test_schema__optional_file__anyof_document_or_null():
    prop = SCHEMA['properties']['f-file']

    document, null_branch = prop['anyOf']
    assert null_branch == {'type': 'null'}
    assert document['type'] == 'object'
    assert sorted(document['properties']) == ['content', 'filename']
    assert sorted(document['required']) == ['content', 'filename']
    assert document['additionalProperties'] is False


def test_schema__required_file__bare_document_object():
    field = OutputField(
        api_name='f-req-file', name='Doc', type='file', is_required=True,
    )

    prop = build_output_schema([field])['properties']['f-req-file']

    assert prop['type'] == 'object'
    assert 'anyOf' not in prop
    assert sorted(prop['required']) == ['content', 'filename']


def test_describe_fields__file_field__states_document_shape():
    assert '"filename": "<name>.md"' in describe_fields(FIELDS)


def test_describe_fields__choice_rule__matches_requiredness():
    prose = describe_fields(FIELDS)

    assert 'Exactly one of: "Yes", "No"' in prose
    assert 'One of (or null): "Good", "Bad"' in prose
    assert 'Any number of: "Skip review", "Notify"' in prose
