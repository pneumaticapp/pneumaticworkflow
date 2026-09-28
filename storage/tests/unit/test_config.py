"""Tests for application configuration."""

import pytest
from pydantic import ValidationError

from src.shared_kernel.config import BaseAppSettings


def test_settings__no_secret_key__raise_error(monkeypatch):
    # arrange
    monkeypatch.delenv('DJANGO_SECRET_KEY', raising=False)

    # act
    with pytest.raises(
        ValidationError,
        match='DJANGO_SECRET_KEY',
    ):
        BaseAppSettings(_env_file=None)


def test_settings__with_secret_key__ok():
    # arrange
    settings = BaseAppSettings(
        DJANGO_SECRET_KEY='test-secret-key',
    )

    # act
    result = settings.DJANGO_SECRET_KEY

    # assert
    assert result == 'test-secret-key'


def test_settings__cors_string__parsed_list():
    # arrange
    settings = BaseAppSettings(
        DJANGO_SECRET_KEY='test-key',
        ALLOWED_ORIGINS='http://a.com,http://b.com',
    )

    # act
    result = settings.ALLOWED_ORIGINS

    # assert
    assert result == [
        'http://a.com',
        'http://b.com',
    ]


def test_settings__cors_list__unchanged():
    # arrange
    settings = BaseAppSettings(
        DJANGO_SECRET_KEY='test-key',
        ALLOWED_ORIGINS=['http://a.com', 'http://b.com'],
    )

    # act
    result = settings.ALLOWED_ORIGINS

    # assert
    assert result == [
        'http://a.com',
        'http://b.com',
    ]


def test_settings__trailing_slash__stripped():
    # arrange
    settings = BaseAppSettings(
        DJANGO_SECRET_KEY='test-key',
        FASTAPI_BASE_URL='http://localhost:8000/',
        BACKEND_PRIVATE_URL='http://backend:8001/',
    )

    # act & assert
    assert settings.FASTAPI_BASE_URL == 'http://localhost:8000'
    assert settings.BACKEND_PRIVATE_URL == 'http://backend:8001'


def test_settings__no_trailing_slash__unchanged():
    # arrange
    settings = BaseAppSettings(
        DJANGO_SECRET_KEY='test-key',
        FASTAPI_BASE_URL='http://localhost:8000',
    )

    # act
    result = settings.FASTAPI_BASE_URL

    # assert
    assert result == 'http://localhost:8000'


def test_settings__check_permission_url__no_double_slash():
    # arrange
    settings = BaseAppSettings(
        DJANGO_SECRET_KEY='test-key',
        BACKEND_PRIVATE_URL='http://backend:8001/',
    )

    # act
    result = settings.check_permission_url

    # assert
    assert '//' not in result.replace('http://', '')


def test_settings__frontend_url__appended_to_cors():
    # arrange
    settings = BaseAppSettings(
        DJANGO_SECRET_KEY='test-key',
        ALLOWED_ORIGINS=['http://a.com'],
        FRONTEND_URL='http://frontend.com',
    )

    # act
    result = settings.ALLOWED_ORIGINS

    # assert
    assert 'http://frontend.com' in result
    assert 'http://a.com' in result


def test_settings__frontend_url_already_in_cors__no_dup():
    # arrange
    settings = BaseAppSettings(
        DJANGO_SECRET_KEY='test-key',
        ALLOWED_ORIGINS=['http://frontend.com'],
        FRONTEND_URL='http://frontend.com',
    )

    # act
    result = settings.ALLOWED_ORIGINS

    # assert
    assert result.count('http://frontend.com') == 1


def test_settings__logs_backend_default__logs_disabled(monkeypatch):
    # arrange
    monkeypatch.delenv('LOGS_BACKEND', raising=False)
    settings = BaseAppSettings(DJANGO_SECRET_KEY='test-key', _env_file=None)

    # act
    result = settings.logs_enabled

    # assert
    assert result is False


def test_settings__logs_backend_empty__logs_disabled():
    """Compose passes an unset LOGS_BACKEND as an empty string."""

    # arrange
    settings = BaseAppSettings(
        DJANGO_SECRET_KEY='test-key',
        LOGS_BACKEND='',
        LOGS_REDIS_URL='redis://:pw@redis:6379/4',
        LOGS_STREAM_MAXLEN=1000,
    )

    # act
    result = settings.logs_enabled

    # assert
    assert result is False


def test_settings__logs_backend_unknown__disabled():
    """The backend writes only to the stores it knows and is off for
    any other value; this service has to agree with it."""

    # arrange
    settings = BaseAppSettings(
        DJANGO_SECRET_KEY='test-key',
        LOGS_BACKEND='loki',
        LOGS_REDIS_URL='redis://:pw@redis:6379/4',
        LOGS_STREAM_MAXLEN=1000,
    )

    # act
    result = settings.logs_enabled

    # assert
    assert result is False


def test_settings__logs_on_all_values__enabled():
    # arrange
    settings = BaseAppSettings(
        DJANGO_SECRET_KEY='test-key',
        LOGS_BACKEND='otlp',
        LOGS_REDIS_URL='redis://:pw@redis:6379/4',
        LOGS_STREAM_MAXLEN=1000,
    )

    # act
    result = settings.logs_enabled

    # assert
    assert result is True


@pytest.mark.parametrize(
    'missing',
    ['LOGS_REDIS_URL', 'LOGS_STREAM_MAXLEN'],
)
def test_settings__logs_on_value_empty__disabled(missing, monkeypatch):
    """No defaults: a store named with an empty buffer setting - the
    way compose passes an unset one - keeps the journal off, the way
    the backend does."""

    # arrange
    values = {
        'LOGS_REDIS_URL': 'redis://:pw@redis:6379/4',
        'LOGS_STREAM_MAXLEN': 1000,
    }
    values[missing] = ''
    monkeypatch.delenv(missing, raising=False)
    settings = BaseAppSettings(
        DJANGO_SECRET_KEY='test-key',
        LOGS_BACKEND='elasticsearch',
        _env_file=None,
        **values,
    )

    # act
    result = settings.logs_enabled

    # assert
    assert result is False


@pytest.mark.parametrize(
    'missing',
    ['LOGS_REDIS_URL', 'LOGS_STREAM_MAXLEN'],
)
def test_settings__logs_on_value_not_passed__disabled(missing, monkeypatch):
    """A buffer setting absent from the environment altogether keeps
    the journal off as well."""

    # arrange
    values = {
        'LOGS_REDIS_URL': 'redis://:pw@redis:6379/4',
        'LOGS_STREAM_MAXLEN': 1000,
    }
    del values[missing]
    monkeypatch.delenv(missing, raising=False)
    settings = BaseAppSettings(
        DJANGO_SECRET_KEY='test-key',
        LOGS_BACKEND='elasticsearch',
        _env_file=None,
        **values,
    )

    # act
    result = settings.logs_enabled

    # assert
    assert result is False


def test_settings__logs_on_elasticsearch_all_values__enabled():
    # arrange
    settings = BaseAppSettings(
        DJANGO_SECRET_KEY='test-key',
        LOGS_BACKEND='elasticsearch',
        LOGS_REDIS_URL='redis://:pw@redis:6379/4',
        LOGS_STREAM_MAXLEN=1000,
        _env_file=None,
    )

    # act
    result = settings.logs_enabled

    # assert
    assert result is True


def test_settings__logs_on_url_not_redis__raise_error():
    # act
    with pytest.raises(ValidationError, match='LOGS_REDIS_URL'):
        BaseAppSettings(
            DJANGO_SECRET_KEY='test-key',
            LOGS_BACKEND='otlp',
            LOGS_REDIS_URL='http://redis:6379/4',
        )


def test_settings__logs_on_rediss_url__accepted():
    # arrange
    settings = BaseAppSettings(
        DJANGO_SECRET_KEY='test-key',
        LOGS_BACKEND='otlp',
        LOGS_REDIS_URL='rediss://:pw@redis:6380/4',
    )

    # act
    result = settings.LOGS_REDIS_URL

    # assert
    assert result == 'rediss://:pw@redis:6380/4'


def test_settings__logs_off_url_not_redis__accepted(monkeypatch):
    """With the pipeline off the URL is never dialled, so it is not
    checked either: a stale value must not stop the service."""

    # arrange
    monkeypatch.delenv('LOGS_BACKEND', raising=False)
    settings = BaseAppSettings(
        DJANGO_SECRET_KEY='test-key',
        LOGS_REDIS_URL='http://redis:6379/4',
        _env_file=None,
    )

    # act
    result = settings.LOGS_REDIS_URL

    # assert
    assert result == 'http://redis:6379/4'
