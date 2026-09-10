from decimal import Decimal
from uuid import UUID

import pytest

from src.logs.events.schema import (
    PAYLOAD_MAX_BYTES,
    PAYLOAD_STR_MAX,
    REDACTED_VALUE,
    normalize_payload,
)
from src.logs.events.tests.fakes import EVENT_TS
from src.utils.logging import SentryLogLevel


def test_normalize_payload__none__empty_dict():

    # act
    result = normalize_payload(None)

    # assert
    assert result == {}


def test_normalize_payload__empty_dict__empty_dict():

    # act
    result = normalize_payload({})

    # assert
    assert result == {}


# One spelling per entry of SECRET_KEY_PARTS plus the shapes a header
# or a camelCase serializer produces (finding F-7 of the review).
@pytest.mark.parametrize(
    'key',
    (
        'password',
        'user_password',
        'passwd',
        'pwd',
        'token',
        'access_token',
        'api_key',
        'api-key',
        'apiKey',
        'X-API-Key',
        'secret',
        'client_secret',
        'Authorization',
        'credentials',
        'private_key',
        'Cookie',
        'session_id',
        'signature',
        'password_salt',
        'bearer',
        'jwt',
        'otp_code',
        'refresh_token',
    ),
)
def test_normalize_payload__secret_key__value_redacted(key):

    # arrange
    payload = {key: 'super-secret-value'}

    # act
    result = normalize_payload(payload)

    # assert
    assert result == {key: REDACTED_VALUE}


def test_normalize_payload__harmless_keys__kept():

    # arrange
    payload = {'name': 'Ann', 'template_id': 12, 'with_attachments': True}

    # act
    result = normalize_payload(payload)

    # assert
    assert result == {
        'name': 'Ann',
        'template_id': 12,
        'with_attachments': True,
    }


def test_normalize_payload__secret_in_a_nested_dict__value_redacted():

    # arrange
    payload = {
        'auth': {'headers': {'token': 'super-secret-value', 'id': 1}},
    }

    # act
    result = normalize_payload(payload)

    # assert
    assert result == {
        'auth': {'headers': '{"token": "[redacted]", "id": 1}'},
    }


def test_normalize_payload__url_with_query__query_dropped():

    """ An access token or a signature rides in the query string. """

    # arrange
    payload = {'url': 'https://api.test/v1/hook?access_token=abc&x=1'}

    # act
    result = normalize_payload(payload)

    # assert
    assert result == {'url': 'https://api.test/v1/hook'}


def test_normalize_payload__url_with_fragment__fragment_kept():

    # arrange
    payload = {'url': 'https://api.test/v1?token=abc#part'}

    # act
    result = normalize_payload(payload)

    # assert
    assert result == {'url': 'https://api.test/v1#part'}


def test_normalize_payload__question_mark_in_plain_text__kept():

    # arrange
    payload = {'name': 'Is it done?'}

    # act
    result = normalize_payload(payload)

    # assert
    assert result == {'name': 'Is it done?'}


def test_normalize_payload__unparsable_url__kept_as_is():

    """ urlsplit raises for a broken IPv6 host: a value that cannot be
        parsed is left alone instead of breaking the whole event. """

    # arrange
    payload = {'url': 'http://[oops?token=abc'}

    # act
    result = normalize_payload(payload)

    # assert
    assert result == {'url': 'http://[oops?token=abc'}


def test_normalize_payload__secret_in_a_too_deep_url__query_dropped():

    # arrange
    payload = {'a': {'b': {'url': 'https://api.test/v1?token=abc'}}}

    # act
    result = normalize_payload(payload)

    # assert
    assert result == {'a': {'b': '{"url": "https://api.test/v1"}'}}


def test_normalize_payload__django_types__serialized():

    # arrange
    key = UUID('12345678-1234-5678-1234-567812345678')
    payload = {
        'created': EVENT_TS,
        'amount': Decimal('10.50'),
        'key': key,
        'items': [EVENT_TS, Decimal('1.10')],
    }

    # act
    result = normalize_payload(payload)

    # assert
    assert result == {
        'created': '2026-09-08T10:15:30.123Z',
        'amount': '10.50',
        'key': '12345678-1234-5678-1234-567812345678',
        'items': ['2026-09-08T10:15:30.123Z', '1.10'],
    }


def test_normalize_payload__long_string__trimmed():

    # arrange
    payload = {'name': 'x' * (PAYLOAD_STR_MAX + 100)}

    # act
    result = normalize_payload(payload)

    # assert
    assert result == {'name': 'x' * PAYLOAD_STR_MAX}


def test_normalize_payload__too_deep_value__json_string():

    # arrange
    payload = {'a': {'b': {'c': 1}}, 'list': [[1, 2]]}

    # act
    result = normalize_payload(payload)

    # assert
    assert result == {'a': {'b': '{"c": 1}'}, 'list': ['[1, 2]']}


def test_normalize_payload__unknown_type__string():

    """ A range is neither a JSON type nor one of the Django ones the
        encoder knows: it is stored as its text. """

    # arrange
    payload = {'obj': range(3)}

    # act
    result = normalize_payload(payload)

    # assert
    assert result == {'obj': 'range(0, 3)'}


def test_normalize_payload__unencodable_value_too_deep__string():

    """ A container the encoder cannot handle becomes its text, so one
        odd value never breaks the whole batch of the sink. """

    # arrange
    payload = {'a': {'b': {'obj': range(3)}}}

    # act
    result = normalize_payload(payload)

    # assert
    assert result == {'a': {'b': '"{\'obj\': range(0, 3)}"'}}


def test_normalize_payload__oversized__replaced_by_size_marker(mocker):

    """ A single event must not be able to fill up the stream: the
        payload is replaced by its size marker, and the loss of an
        audit payload is reported (throttled, an emitter loop would
        flood Sentry). 40 keys of 1000 bytes plus the JSON syntax
        make 40550 bytes. """

    # arrange
    payload = {f'key_{num}': 'x' * 1000 for num in range(40)}
    report_error_mock = mocker.patch(
        'src.logs.events.schema.report_error',
    )

    # act
    result = normalize_payload(payload)

    # assert
    assert result == {'_truncated': True, '_size': 40550}
    report_error_mock.assert_called_once_with(
        'Event payload dropped: over the size limit',
        {'size': 40550, 'limit': PAYLOAD_MAX_BYTES},
        level=SentryLogLevel.WARNING,
    )


def test_normalize_payload__at_the_size_limit__kept(mocker):

    """ The limit is the largest payload that is still stored whole:
        the marker replaces only a bigger one. 16 keys of 2000 bytes
        make 32224 bytes with the JSON syntax, the pad key of 533
        bytes brings the total to exactly PAYLOAD_MAX_BYTES. """

    # arrange
    payload = {f'key_{num:02d}': 'x' * 2000 for num in range(16)}
    payload['pad'] = 'y' * 533
    report_error_mock = mocker.patch(
        'src.logs.events.schema.report_error',
    )

    # act
    result = normalize_payload(payload)

    # assert
    assert result == payload
    assert result is not payload
    report_error_mock.assert_not_called()
