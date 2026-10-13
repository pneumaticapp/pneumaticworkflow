import json

from pytest_django.fixtures import SettingsWrapper

from src.utils.redaction import redact_event
from src.utils.logging import sentry_before_send


def test_redaction__oauth_request_celery_vars_and_spans__no_secrets(
    mcp_settings: SettingsWrapper,
):
    # arrange
    file_secret = mcp_settings.MCP_FILE_SERVICE_SECRET
    event = {
        'request': {
            'url': 'https://pneumatic.test/oauth/mcp/token?code=CODE_SECRET',
            'headers': {
                'Authorization': 'Bearer mcp-d_DELEGATION_SECRET',
                'X-MCP-File-Service-Secret': file_secret,
            },
            'data': {'refresh_token': 'REFRESH_SECRET'},
        },
        'exception': {
            'values': [
                {
                    'stacktrace': {
                        'frames': [
                            {
                                'vars': {
                                    'supplied': 'FRAME_SECRET',
                                    'expected': 'EXPECTED_SECRET',
                                },
                            },
                        ],
                    },
                },
            ],
        },
        'breadcrumbs': {
            'values': [
                {
                    'message': (
                        'https://files.test/files/mcp/download/TICKET_SECRET'
                    ),
                    'data': {'credential': 'CREDENTIAL_SECRET'},
                },
            ],
        },
        'spans': [{'description': 'https://remote.test/import?q=URL_SECRET'}],
        'extra': {
            'source_url': 'https://remote.test/path?query=SOURCE_SECRET',
        },
    }

    # act
    cleaned = sentry_before_send(event=event, hint={})
    trace = redact_event(event=event, hint={})
    serialized = json.dumps(cleaned)

    # assert
    assert cleaned == trace
    assert 'CODE_SECRET' not in serialized
    assert 'REFRESH_SECRET' not in serialized
    assert 'FRAME_SECRET' not in serialized
    assert 'EXPECTED_SECRET' not in serialized
    assert 'TICKET_SECRET' not in serialized
    assert 'URL_SECRET' not in serialized
    assert 'SOURCE_SECRET' not in serialized
    assert 'CREDENTIAL_SECRET' not in serialized
    assert mcp_settings.MCP_FILE_SERVICE_SECRET not in serialized


def test_redaction__ordinary_event__preserves_diagnostics():
    # arrange
    event = {
        'request': {'url': 'https://pneumatic.test/templates'},
        'extra': {'data': {'template_id': 123}},
        'exception': {'vars': {'count': 2}},
    }

    # act
    cleaned = redact_event(event=event)

    # assert
    assert cleaned == event


def test_redaction__delegated_backend_event__strips_frame_secrets():
    # arrange
    event = {
        'tags': {'mcp': 'true'},
        'request': {'url': 'https://pneumatic.test/templates'},
        'exception': {'vars': {'supplied': 'FRAME_SECRET'}},
        'extra': {'data': {'token': 'SOURCE_SECRET'}},
    }

    # act
    cleaned = redact_event(event=event)

    # assert
    serialized = json.dumps(cleaned)
    assert 'FRAME_SECRET' not in serialized
    assert 'SOURCE_SECRET' not in serialized


def test_redaction__private_header_without_url__strips_frame_secrets():
    # arrange
    event = {
        'request': {'headers': {'X-MCP-Service-Secret': 'HEADER_SECRET'}},
        'exception': {
            'stacktrace': {
                'frames': [
                    {'vars': {'expected': 'FRAME_SECRET'}},
                ],
            },
        },
    }

    # act
    cleaned = redact_event(event=event)
    serialized = json.dumps(cleaned)

    # assert
    assert 'HEADER_SECRET' not in serialized
    assert 'FRAME_SECRET' not in serialized
