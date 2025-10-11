import pytest
from src.generics.mixins.managers import SearchSqlQueryMixin


def test_get_tsquery__normal_text__ok():
    mixin = SearchSqlQueryMixin()
    mixin.search_text = "normal search text"

    tsquery_sql, tsquery_params = mixin._get_tsquery()

    assert mixin.search_text == "normal search text"
    assert "%(" in tsquery_sql
    assert tsquery_params == {
        'search_0': 'normal',
        'search_1': 'search',
        'search_2': 'text',
    }


@pytest.mark.parametrize(
    "injection,expected_params", [
        (
            "'; DROP 'test\\':",
            {
                'search_0': "'';",
                'search_1': 'DROP',
                'search_2': "''test\\\\''\\:",
            },
        ),
        (
            "1' OR '1'='1 test",
            {
                'search_0': "1''",
                'search_1': 'OR',
                'search_2': "''1''=''1",
                'search_3': 'test',
            },
        ),
        (
            "test'--",
            {
                'search_0': "test''--",
            },
        ),
        (
            "test ' UNION SELECT * FROM accounts_user --",
            {
                'search_0': 'test',
                'search_1': "''",
                'search_2': 'UNION',
                'search_3': 'SELECT',
                'search_4': '*',
                'search_5': 'FROM',
                'search_6': 'accounts_user',
                'search_7': '--',
            },
        ),
        (
            "\\'; DELETE FROM processes_task; -- test",
            {
                'search_0': "\\\\'';",
                'search_1': 'DELETE',
                'search_2': 'FROM',
                'search_3': 'processes_task;',
                'search_4': '--',
                'search_5': 'test',
            },
        ),
        (
            "test'); INSERT INTO users VALUES ('hack'); --",
            {
                'search_0': "test''\\);",
                'search_1': 'INSERT',
                'search_2': 'INTO',
                'search_3': 'users',
                'search_4': 'VALUES',
                'search_5': "\\(''hack''\\);",
                'search_6': '--',
            },
        ),
    ],
)
def test_get_tsquery__sql_injection_protection__ok(injection, expected_params):
    mixin = SearchSqlQueryMixin()
    mixin.search_text = injection

    tsquery_sql, tsquery_params = mixin._get_tsquery()

    assert mixin.search_text == injection
    assert "%(" in tsquery_sql
    assert tsquery_params == expected_params


@pytest.mark.parametrize(
    "text_with_quotes,escaped_quotes", [
        ("user's data", {'search_0': "user''s", 'search_1': 'data'}),
        ("normal text", {'search_0': 'normal', 'search_1': 'text'}),
        ("test''quotes", {'search_0': "test''''quotes"}),
    ],
)
def test_get_tsquery__single_quotes__ok(text_with_quotes, escaped_quotes):
    mixin = SearchSqlQueryMixin()
    mixin.search_text = text_with_quotes

    tsquery_sql, tsquery_params = mixin._get_tsquery()

    assert mixin.search_text == text_with_quotes
    assert "%(" in tsquery_sql
    assert tsquery_params == escaped_quotes


def test_get_tsquery__empty_text__ok():
    mixin = SearchSqlQueryMixin()
    mixin.search_text = ""

    tsquery_sql, tsquery_params = mixin._get_tsquery()

    assert mixin.search_text == ""
    assert "%(" in tsquery_sql
    assert tsquery_params == {'search_0': ''}


def test_get_tsquery__single_word__ok():
    mixin = SearchSqlQueryMixin()
    mixin.search_text = "single"

    tsquery_sql, tsquery_params = mixin._get_tsquery()

    assert mixin.search_text == "single"
    assert "%(" in tsquery_sql
    assert tsquery_params == {'search_0': 'single'}
