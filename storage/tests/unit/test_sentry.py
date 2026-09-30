"""Tests for Sentry initialization and event filtering."""

from typing import Any
from unittest.mock import patch

import pytest

from src.shared_kernel.config import ProductionSettings, get_settings
from src.shared_kernel.exceptions import (
    AuthenticationError,
    FileAccessDeniedError,
    PermissionDeniedError,
)
from src.shared_kernel.sentry import (
    init_sentry,
    sentry_before_send,
    traces_sampler,
)


def _exc_hint(exc: BaseException) -> dict[str, Any]:
    return {'exc_info': (type(exc), exc, None)}


@pytest.fixture
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_sentry_before_send__authentication_error__dropped():
    # arrange
    event = {'event_id': '1'}
    hint = _exc_hint(AuthenticationError())

    # act
    result = sentry_before_send(event, hint)

    # assert
    assert result is None


def test_sentry_before_send__permission_denied_error__dropped():
    # arrange
    event = {'event_id': '1'}
    hint = _exc_hint(PermissionDeniedError())

    # act
    result = sentry_before_send(event, hint)

    # assert
    assert result is None


def test_sentry_before_send__file_access_denied_error__dropped():
    # arrange
    event = {'event_id': '1'}
    hint = _exc_hint(FileAccessDeniedError(file_id='file-1', user_id=1))

    # act
    result = sentry_before_send(event, hint)

    # assert
    assert result is None


def test_sentry_before_send__unexpected_exception__event_returned():
    # arrange
    event = {'event_id': '1'}
    hint = _exc_hint(ValueError('boom'))

    # act
    result = sentry_before_send(event, hint)

    # assert
    assert result is event


def test_sentry_before_send__no_exc_info__event_returned():
    # arrange
    event = {'event_id': '1'}

    # act
    result = sentry_before_send(event, hint={})

    # assert
    assert result is event


def test_traces_sampler__head_request__zero():
    # arrange
    sampling_context = {'asgi_scope': {'type': 'http', 'method': 'HEAD'}}

    # act
    result = traces_sampler(sampling_context)

    # assert
    assert result == 0


def test_traces_sampler__options_request__zero():
    # arrange
    sampling_context = {'asgi_scope': {'type': 'http', 'method': 'OPTIONS'}}

    # act
    result = traces_sampler(sampling_context)

    # assert
    assert result == 0


def test_traces_sampler__get_request__configured_sample_rate(
    monkeypatch,
    clear_settings_cache,
):
    # arrange
    monkeypatch.setenv('DJANGO_SECRET_KEY', 'test-secret-key')
    monkeypatch.setenv('SENTRY_TRACES_SAMPLE_RATE', '0.2')
    sampling_context = {'asgi_scope': {'type': 'http', 'method': 'GET'}}

    # act
    result = traces_sampler(sampling_context)

    # assert
    assert result == 0.2


def test_traces_sampler__rate_not_configured__zero(
    monkeypatch,
    clear_settings_cache,
):
    # arrange
    monkeypatch.setenv('DJANGO_SECRET_KEY', 'test-secret-key')
    monkeypatch.delenv('SENTRY_TRACES_SAMPLE_RATE', raising=False)
    sampling_context = {'asgi_scope': {'type': 'http', 'method': 'GET'}}

    # act
    result = traces_sampler(sampling_context)

    # assert
    assert result == 0


def test_traces_sampler__non_http_scope__zero():
    # arrange
    sampling_context = {'asgi_scope': {'type': 'lifespan'}}

    # act
    result = traces_sampler(sampling_context)

    # assert
    assert result == 0


def test_settings__production__traces_enabled():
    # arrange
    settings = ProductionSettings(DJANGO_SECRET_KEY='test-secret-key')

    # act
    result = settings.SENTRY_TRACES_SAMPLE_RATE

    # assert
    assert result == 0.2


def test_init_sentry__dsn_not_set__init_not_called(
    monkeypatch,
    clear_settings_cache,
):
    # arrange
    monkeypatch.setenv('DJANGO_SECRET_KEY', 'test-secret-key')
    monkeypatch.delenv('SENTRY_DSN', raising=False)

    # act
    with patch('src.shared_kernel.sentry.sentry_sdk.init') as init_mock:
        init_sentry()

    # assert
    init_mock.assert_not_called()


def test_init_sentry__dsn_set__init_called_with_expected_kwargs(
    monkeypatch,
    clear_settings_cache,
):
    # arrange
    dsn = 'https://key@sentry.example.com/1'
    environment = 'production'
    monkeypatch.setenv('DJANGO_SECRET_KEY', 'test-secret-key')
    monkeypatch.setenv('SENTRY_DSN', dsn)
    monkeypatch.setenv('SENTRY_ENVIRONMENT', environment)

    # act
    with patch('src.shared_kernel.sentry.sentry_sdk.init') as init_mock:
        init_sentry()

    # assert
    init_mock.assert_called_once()
    kwargs = init_mock.call_args.kwargs
    assert kwargs['dsn'] == dsn
    assert kwargs['environment'] == environment
    assert kwargs['send_default_pii'] is True
    assert kwargs['traces_sampler'] is traces_sampler
    assert kwargs['before_send'] is sentry_before_send
    assert len(kwargs['integrations']) == 2
