from datetime import (
    datetime,
    timezone,
)

import pytest

from src.ai.performers.output_fields import STRING_MAX_LENGTH
from src.ai.performers.output_translation import (
    IncompleteOutputError,
    to_pneumatic_output,
)
from src.ai.tests.performers.fixtures import fillable_fields

FIELDS = fillable_fields()


def _utc_timestamp(iso_text):
    parsed = datetime.fromisoformat(iso_text)
    return parsed.replace(tzinfo=timezone.utc).timestamp()


def test_translate__every_type__task_complete_format():
    output = to_pneumatic_output(
        fields=FIELDS,
        data={
            'f-text': 'Looks good',
            'f-str': '1.2.3',
            'f-url': 'https://example.com/pr/1',
            'f-date': '2026-07-10',
            'f-num': 42,
            'f-radio': 'Yes',
            'f-opt-radio': 'Bad',
            'f-check': ['Notify'],
        },
    )

    assert output['f-text'] == 'Looks good'
    assert output['f-str'] == '1.2.3'
    assert output['f-url'] == 'https://example.com/pr/1'
    assert output['f-date'] == _utc_timestamp('2026-07-10T12:00:00')
    assert output['f-num'] == 42
    assert output['f-radio'] == 'Yes'
    assert output['f-opt-radio'] == 'Bad'
    assert output['f-check'] == ['Notify']


def test_translate__bare_date__pinned_to_noon_utc():
    output = to_pneumatic_output(
        fields=FIELDS,
        data={'f-str': 'v', 'f-radio': 'Yes', 'f-date': '2026-07-10'},
    )

    rendered = datetime.fromtimestamp(output['f-date'], tz=timezone.utc)
    assert rendered.isoformat() == '2026-07-10T12:00:00+00:00'


def test_translate__full_datetime__passed_through_unpinned():
    output = to_pneumatic_output(
        fields=FIELDS,
        data={
            'f-str': 'v',
            'f-radio': 'Yes',
            'f-date': '2026-07-10T08:30:00Z',
        },
    )

    assert output['f-date'] == _utc_timestamp('2026-07-10T08:30:00')


def test_translate__overlong_string__truncated():
    output = to_pneumatic_output(
        fields=FIELDS,
        data={'f-str': 'x' * 500, 'f-radio': 'Yes'},
    )

    assert len(output['f-str']) == STRING_MAX_LENGTH


def test_translate__blank_optional_fields__omitted():
    output = to_pneumatic_output(
        fields=FIELDS,
        data={
            'f-text': None,
            'f-str': '1.0.0',
            'f-url': '',
            'f-date': None,
            'f-num': None,
            'f-radio': 'No',
            'f-opt-radio': None,
            'f-check': [],
        },
    )

    assert sorted(output) == ['f-radio', 'f-str']


def test_translate__resolved_file_field__markdown_links_pass_through():
    links = ['[report.md](https://my.pneumatic.app/files/uuid-1)']

    output = to_pneumatic_output(
        fields=FIELDS,
        data={'f-str': '1.0', 'f-radio': 'Yes', 'f-file': links},
    )

    assert output['f-file'] == links


def test_translate__unresolved_file_value__rejected_not_forwarded():
    output = to_pneumatic_output(
        fields=FIELDS,
        data={
            'f-str': '1.0',
            'f-radio': 'Yes',
            'f-file': {'filename': 'x.md', 'content': 'body'},
        },
    )

    assert 'f-file' not in output


def test_translate__unusable_optional_value__dropped_not_fatal():
    output = to_pneumatic_output(
        fields=FIELDS,
        data={
            'f-str': '1.0.0',
            'f-radio': 'Yes',
            'f-url': 'not a url',
            'f-num': 'abc',
        },
    )

    assert 'f-url' not in output
    assert 'f-num' not in output
    assert output['f-radio'] == 'Yes'


@pytest.mark.parametrize(
    'data', [
        # missing required string
        {'f-radio': 'Yes'},
        # hallucinated choice value on a required radio
        {'f-str': '1.0', 'f-radio': 'Maybe'},
        # null required radio
        {'f-str': '1.0', 'f-radio': None},
        # empty model response
        {},
    ],
)
def test_translate__unusable_required_field__aborts(data):
    with pytest.raises(IncompleteOutputError):
        to_pneumatic_output(fields=FIELDS, data=data)


def test_translate__incomplete_output_error__lists_every_problem():
    with pytest.raises(IncompleteOutputError) as ex:
        to_pneumatic_output(fields=FIELDS, data={})

    # f-str and f-radio are the two required fields
    assert len(ex.value.problems) == 2
