import pytest

from src.ai.performers.generated_files import (
    resolve_generated_files,
    sanitize_filename,
)
from src.ai.performers.output_fields import OutputField
from src.ai.performers.output_translation import IncompleteOutputError
from src.processes.enums import FieldType


def _field(api_name='report', field_type=FieldType.FILE, is_required=True):
    return OutputField(
        api_name=api_name,
        name='Report',
        type=field_type,
        is_required=is_required,
    )


def test_sanitize_filename__link_breaking_chars__stripped():
    assert sanitize_filename(
        'we[ird]:na(me)/x.md',
        fallback='f.md',
    ) == 'weirdnamex.md'


def test_sanitize_filename__no_extension__md_appended():
    assert sanitize_filename('summary', fallback='f.md') == 'summary.md'


def test_sanitize_filename__uppercase_extension__kept():
    assert sanitize_filename('REPORT.MD', fallback='f.md') == 'REPORT.MD'


def test_sanitize_filename__blank__fallback():
    assert sanitize_filename('   ', fallback='report.md') == 'report.md'


def test_resolve__document__uploaded_and_rewritten():
    uploads = []

    def upload(filename, content):
        uploads.append((filename, content))
        return 'https://files.test/gen12345xyz'

    result = resolve_generated_files(
        fields=[_field()],
        data={'report': {'filename': 'summary.md', 'content': '# Hi'}},
        upload=upload,
    )

    assert uploads == [('summary.md', '# Hi')]
    assert result == {
        'report': ['[summary.md](https://files.test/gen12345xyz)'],
    }


def test_resolve__other_fields__pass_through():
    def upload(filename, content):  # pragma: no cover
        raise AssertionError('must not upload')

    result = resolve_generated_files(
        fields=[_field(api_name='summary', field_type=FieldType.TEXT)],
        data={'summary': 'text value'},
        upload=upload,
    )

    assert result == {'summary': 'text value'}


def test_resolve__null_file_value__untouched():
    def upload(filename, content):  # pragma: no cover
        raise AssertionError('must not upload')

    result = resolve_generated_files(
        fields=[_field(is_required=False)],
        data={'report': None},
        upload=upload,
    )

    assert result == {'report': None}


def test_resolve__required_bad_shape__incomplete_output():
    def upload(filename, content):  # pragma: no cover
        raise AssertionError('must not upload')

    with pytest.raises(IncompleteOutputError) as ex:
        resolve_generated_files(
            fields=[_field()],
            data={'report': 'just a string'},
            upload=upload,
        )

    assert 'Report' in ex.value.problems[0]
    assert '{filename, content}' in ex.value.problems[0]


def test_resolve__required_empty_content__incomplete_output():
    def upload(filename, content):  # pragma: no cover
        raise AssertionError('must not upload')

    with pytest.raises(IncompleteOutputError):
        resolve_generated_files(
            fields=[_field()],
            data={'report': {'filename': 'a.md', 'content': '   '}},
            upload=upload,
        )


def test_resolve__optional_bad_shape__dropped():
    def upload(filename, content):  # pragma: no cover
        raise AssertionError('must not upload')

    result = resolve_generated_files(
        fields=[_field(is_required=False)],
        data={'report': ['unexpected', 'list']},
        upload=upload,
    )

    assert result == {'report': None}


def test_resolve__unusable_filename__api_name_fallback():
    def upload(filename, content):
        return 'https://files.test/gen12345xyz'

    result = resolve_generated_files(
        fields=[_field()],
        data={'report': {'filename': '///', 'content': 'text'}},
        upload=upload,
    )

    assert result == {
        'report': ['[report.md](https://files.test/gen12345xyz)'],
    }


def test_resolve__upload_error__propagates():
    def upload(filename, content):
        raise RuntimeError('service down')

    with pytest.raises(RuntimeError):
        resolve_generated_files(
            fields=[_field()],
            data={'report': {'filename': 'a.md', 'content': 'text'}},
            upload=upload,
        )
