import pytest
from datetime import timedelta
from pneumatic_backend.processes.utils.common import (
    is_tasks_ordering_correct,
    string_abbreviation,
    insert_fields_values_to_text,
    get_duration_format,
)


class TestCorrectOrdering:
    def test_ordering_correct(self):
        data = [1, 2, 3, 4, 5]
        result = is_tasks_ordering_correct(data)

        assert result is True

    def test_ordering_multiple_values(self):
        data = [1, 2, 2, 3, 4, 5]
        result = is_tasks_ordering_correct(data)

        assert result is False

    def test_ordering_incorrect(self):
        data = [1, 2, 4, 5]
        result = is_tasks_ordering_correct(data)

        assert result is False


class TestStringCut:
    def test_not_cut(self):
        length = 10
        s = '1234567890'
        result = string_abbreviation(s, length)

        assert len(result) == length
        assert result == s

    def test_cut(self):
        length = 9
        s = '1234567890'
        result = string_abbreviation(s, length)

        assert len(result) == length
        assert result == '12345678…'

    def test_postfix(self):
        length = 12
        s = '1234567890'
        postfix = '11'
        result = string_abbreviation(s, length, postfix)

        assert len(result) == length
        assert result == '123456789011'

    def test_postfix_cut(self):
        length = 10
        s = '1234567890'
        postfix = '11'
        result = string_abbreviation(s, length, postfix)

        assert len(result) == length
        assert result == '1234567…11'

    def test_name_none(self):
        length = 10
        result = string_abbreviation(None, length)

        assert result == ''

    def test_name_none_with_postfix(self):
        length = 10
        postfix = '123'
        result = string_abbreviation(None, length, postfix)

        assert result == postfix

    def test_name_none_long_postfix(self):
        length = 5
        postfix = '1234567890'
        result = string_abbreviation(None, length, postfix)

        assert len(result) == length
        assert result == '12345'

    def test_without_delimeter(self):
        length = 15
        s = 'new-kickoff-name'
        postfix = '-4353'
        result = string_abbreviation(s, length, postfix, False)

        assert len(result) == length
        assert result == 'new-kickof-4353'


class TestInsertValueToText:
    def test_insert(self):
        text = 'My name is {{name}}. I was born in {{city}}'
        values = {'name': 'Andre', 'city': 'Boston'}
        result = insert_fields_values_to_text(text, values)

        assert result == 'My name is Andre. I was born in Boston'

    def test_insert_values_missed(self):
        text = 'My name is {{name}}. I was born in {{city}}'
        values = {'name': 'Andre'}
        result = insert_fields_values_to_text(text, values)

        assert result == 'My name is Andre. I was born in {{city}}'

    def test_insert_values_with_spaces(self):
        text = 'My name is {{ name}}. I was born in {{  city  }}'
        values = {'name': 'Andre', 'city': 'Boston'}
        result = insert_fields_values_to_text(text, values)

        assert result == 'My name is Andre. I was born in Boston'

    def test_insert_values_no_text(self):
        text = ''
        values = {'name': 'Andre', 'city': 'Boston'}
        result = insert_fields_values_to_text(text, values)

        assert result == ''

    def test_insert_no_values(self):
        text = 'My name is {{ name}}. I was born in {{  city  }}'
        values = {}
        result = insert_fields_values_to_text(text, values)

        assert result == text

    def test_insert_different_values(self):
        text = 'My name is {{ name}}. I was born in {{city  }}'
        values = {'name': 'Andre', 'city': 'Boston'}
        result = insert_fields_values_to_text(text, values)

        assert result == 'My name is Andre. I was born in Boston'


class TestGetDurationFormat:
    @pytest.mark.parametrize(
        ('duration', 'expected_str'),
        [
            (timedelta(seconds=59), 'Less than 1 minute'),
            (timedelta(seconds=75), '1 minute'),
            (timedelta(seconds=123), '2 minutes'),
            (timedelta(seconds=3601), '1 hour 0 minutes'),
            (timedelta(seconds=3783), '1 hour 3 minutes'),
            (timedelta(seconds=7260), '2 hours 1 minute'),
            (timedelta(seconds=86400), '1 day 0 hours 0 minutes'),
            (timedelta(seconds=172800), '2 days 0 hours 0 minutes'),
            (timedelta(seconds=90000), '1 day 1 hour 0 minutes'),
        ]
    )
    def test_ok(self, duration, expected_str):
        # act
        result = get_duration_format(duration)
        # assert
        assert result == expected_str
