"""Capabilities and signed URL queries cannot escape via logs or Sentry."""

import logging

from uvicorn.logging import AccessFormatter

from src.shared_kernel.security.redaction import (
    RedactionFilter,
    redact_data,
    redact_text,
)
from src.shared_kernel.sentry import sentry_before_send


def test_access__request_target_and_external_query_redacted__ok():
    # arrange

    # act
    text = redact_text(
        'GET /files/mcp/download/opaque-secret?auth=hidden HTTP/1.1 '
        'https://external.example/file?X-Amz-Signature=signed-secret',
    )

    # assert
    assert 'opaque-secret' not in text
    assert 'hidden' not in text
    assert 'signed-secret' not in text
    assert '/files/mcp/download/[redacted]' in text


def test_formatted__access_log_filtered__ok():
    # arrange
    record = logging.LogRecord(
        'uvicorn.access',
        logging.INFO,
        __file__,
        1,
        '%s %s',
        ('GET', '/mcp/download/ticket-secret?token=hidden'),
        None,
    )

    # act
    result = RedactionFilter().filter(record=record)

    # assert
    assert result
    assert 'ticket-secret' not in record.getMessage()
    assert 'hidden' not in record.getMessage()


def test_nested__sentry_event_redacted_and_identity_preserved__ok():
    # arrange
    event = {
        'request': {
            'url': 'https://app.example/files/mcp/download/ticket-secret',
            'query_string': 'code=login-secret',
            'headers': {'Authorization': 'Bearer storage-secret'},
            'data': {
                'url': 'https://external.example/a?key=query-secret',
                'credential': 'mcp-u_opaque-secret',
            },
        }
    }

    # act
    result = sentry_before_send(event=event, hint={})

    # assert
    assert result is event
    assert 'ticket-secret' not in str(result)
    assert 'login-secret' not in str(result)
    assert 'storage-secret' not in str(result)
    assert 'query-secret' not in str(result)
    assert 'opaque-secret' not in str(result)


def test_header__pairs_redacted__ok():
    # arrange

    # act
    result = redact_data([['Authorization', 'secret']])

    # assert
    assert result == [
        ['Authorization', '[redacted]'],
    ]


def test_ticket__key_and_validation_input_redacted__ok():
    # arrange
    value = {
        'ticket': 'opaque-ticket-secret',
        'errors': [
            {
                'loc': ('path', 'ticket'),
                'input': 'opaque-ticket-secretx',
                'msg': 'String should have at most 43 characters',
            }
        ],
    }

    # act
    sanitized = redact_data(value)

    # assert
    assert 'opaque-ticket-secret' not in str(sanitized)
    assert sanitized['errors'][0]['input'] == '[redacted]'


def test_real__uvicorn_access_formatter_keeps_argument_shape__ok():
    # arrange
    record = logging.LogRecord(
        'uvicorn.access',
        logging.INFO,
        __file__,
        1,
        '%s - "%s %s HTTP/%s" %d',
        (
            '127.0.0.1:1234',
            'GET',
            '/mcp/download/ticket-secret?code=login-secret',
            '1.1',
            200,
        ),
        None,
    )

    # act
    result = RedactionFilter().filter(record=record)

    # assert
    assert result
    formatted = AccessFormatter(
        '%(client_addr)s %(request_line)s %(status_code)s',
        use_colors=False,
    ).format(record)
    assert 'ticket-secret' not in formatted
    assert 'login-secret' not in formatted
    assert '200' in formatted


def test_exception__argument_query_is_redacted__ok():
    # arrange
    record = logging.LogRecord(
        'src.shared_kernel.exceptions.exception_handler',
        logging.ERROR,
        __file__,
        1,
        'Unexpected error: %s',
        (RuntimeError('https://source.example/a?secret=hidden'),),
        None,
    )

    # act
    result = RedactionFilter().filter(record=record)

    # assert
    assert result
    assert 'hidden' not in record.getMessage()
