"""Enabled MCP must have a private core origin and a strong service secret."""

from collections.abc import Callable
from typing import Any

import pytest
from pydantic import ValidationError

from src.shared_kernel.config import BaseAppSettings


def test_mcp__defaults_disabled_and_core_proxy__ok(
    monkeypatch: pytest.MonkeyPatch,
):
    # arrange
    monkeypatch.delenv('MCP_ENABLED', raising=False)
    monkeypatch.delenv('MCP_BACKEND_URL', raising=False)

    # act
    settings = BaseAppSettings(_env_file=None, DJANGO_SECRET_KEY='test-key')

    # assert
    assert settings.MCP_ENABLED is False
    assert settings.MCP_BACKEND_URL == 'http://pneumatic-nginx'


@pytest.mark.parametrize(
    ('value', 'expected'),
    [
        (None, False),
        ('no', False),
        ('yes', True),
        ('', False),
        ('true', False),
        ('unexpected', False),
    ],
)
def test_mcp__enabled_env_without_strict_validation__ok(
    monkeypatch: pytest.MonkeyPatch,
    value: str | None,
    expected: bool,
):
    # arrange
    if value is None:
        monkeypatch.delenv('MCP_ENABLED', raising=False)
    else:
        monkeypatch.setenv('MCP_ENABLED', value)

    # act
    settings = BaseAppSettings(
        _env_file=None,
        DJANGO_SECRET_KEY='test-key',
        MCP_FILE_SERVICE_SECRET='x' * 32,
    )

    # assert
    assert settings.MCP_ENABLED is expected


@pytest.mark.parametrize('secret', ['', 'x' * 31, ' ' * 32])
def test_enabled__mcp_rejects_missing_or_short_secret__ok(secret: str):
    # arrange

    # act
    with pytest.raises(ValidationError) as ex:
        BaseAppSettings(
            _env_file=None,
            DJANGO_SECRET_KEY='test-key',
            MCP_ENABLED=True,
            MCP_FILE_SERVICE_SECRET=secret,
        )

    # assert
    assert ex.value.errors(include_input=False)[0]['msg'] == (
        'Value error, MCP_FILE_SERVICE_SECRET must contain at least '
        '32 characters'
    )


@pytest.mark.parametrize(
    'url',
    [
        'http://pneumatic-nginx/',
        'http://core.internal:8001',
        'https://backend.namespace.svc.cluster.local',
        'http://10.0.0.1:8001',
        'http://127.0.0.1:8001',
        'http://[fd00::1]:8001',
    ],
)
def test_enabled__mcp_accepts_private_origin__ok(
    url: str, mcp_settings: Callable[..., Any]
):
    # arrange

    # act
    settings = mcp_settings(MCP_BACKEND_URL=url)
    expected_url = url.rstrip('/')

    # assert
    assert expected_url == settings.MCP_BACKEND_URL


@pytest.mark.parametrize(
    'url',
    [
        '',
        'pneumatic-nginx',
        'ftp://pneumatic-nginx',
        'http://user:secret@pneumatic-nginx',
        'http://pneumatic-nginx/path',
        'http://pneumatic-nginx?credential=secret',
        'http://pneumatic-nginx#fragment',
        'http://pneumatic-nginx:99999',
        'http://pneumatic-nginx:0',
        'http://pneumatic-nginx?',
        'http://pneumatic-nginx#',
        'http://0x08080808',
        'http://8.8.8.8',
        'http://example.com',
        'http://169.254.169.254',
        'http://0.0.0.0',
        'http://[::]',
        'http://pneumatic-nginx\\evil',
        'http://pneumatic-nginx\n',
    ],
)
def test_enabled__mcp_rejects_unsafe_or_malformed_origin__denied(
    url: str, mcp_settings: Callable[..., Any]
):
    # arrange

    # act
    with pytest.raises(ValidationError) as ex:
        mcp_settings(MCP_BACKEND_URL=url)

    # assert
    assert ex.value.errors(include_input=False)[0]['msg'] == (
        'Value error, MCP_BACKEND_URL must be a private HTTP(S) origin '
        'without credentials'
    )


def test_disabled__mcp_allows_unconfigured_values__ok():
    # arrange

    # act
    settings = BaseAppSettings(
        _env_file=None,
        DJANGO_SECRET_KEY='test-key',
        MCP_ENABLED=False,
        MCP_BACKEND_URL='not-configured',
        MCP_FILE_SERVICE_SECRET='',
    )

    # assert
    assert settings.MCP_ENABLED is False


def test_config__failure_does_not_print_supplied_secret__denied():
    # arrange
    secret = 'private-long-secret-never-print-1234'

    # act
    with pytest.raises(ValidationError) as error:
        BaseAppSettings(
            _env_file=None,
            DJANGO_SECRET_KEY='test-key',
            MCP_ENABLED=True,
            MCP_BACKEND_URL='http://example.com',
            MCP_FILE_SERVICE_SECRET=secret,
        )

    # assert
    assert secret not in str(error.value)


@pytest.mark.parametrize('limit', [1, 1024, 25 * 1024 * 1024])
def test_import__limit_within_hard_cap__ok(
    limit: int, mcp_settings: Callable[..., Any]
):
    # arrange

    # act
    settings = mcp_settings(MCP_MAX_IMPORT_BYTES=limit)

    # assert
    assert limit == settings.MCP_MAX_IMPORT_BYTES


@pytest.mark.parametrize('limit', [0, -1, 25 * 1024 * 1024 + 1])
def test_import__limit_outside_hard_cap_denied__denied(
    limit: int, mcp_settings: Callable[..., Any]
):
    # arrange

    # act
    with pytest.raises(ValidationError) as ex:
        mcp_settings(MCP_MAX_IMPORT_BYTES=limit)

    # assert
    assert ex.value.errors(include_input=False)[0]['loc'] == (
        'MCP_MAX_IMPORT_BYTES',
    )
