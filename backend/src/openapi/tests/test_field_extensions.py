from src.generics.fields import DocCharField, DocChoiceField
from src.openapi.field_extensions import DocExampleFieldExtension


def test_doc_char_field__stores_example():
    field = DocCharField(max_length=200, example='need_comments')

    assert field.example == 'need_comments'
    assert field.max_length == 200
    assert field.to_internal_value('need_comments') == 'need_comments'


def test_doc_example_field_extension__adds_example(mocker):
    field = DocCharField(max_length=200, example='need_comments')
    auto_schema = mocker.Mock()
    auto_schema._map_serializer_field.return_value = {
        'type': 'string',
        'maxLength': 200,
    }
    extension = DocExampleFieldExtension(field)

    result = extension.map_serializer_field(auto_schema, 'response')

    auto_schema._map_serializer_field.assert_called_once_with(
        field,
        'response',
        bypass_extensions=True,
    )
    assert result == {
        'type': 'string',
        'maxLength': 200,
        'example': 'need_comments',
    }


def test_doc_example_field_extension__no_example__keeps_schema(mocker):
    field = DocChoiceField(choices=(('equal', 'Equal'),))
    auto_schema = mocker.Mock()
    mapped = {'type': 'string', 'enum': ['equal']}
    auto_schema._map_serializer_field.return_value = mapped
    extension = DocExampleFieldExtension(field)

    result = extension.map_serializer_field(auto_schema, 'response')

    assert result == mapped
    assert 'example' not in result
