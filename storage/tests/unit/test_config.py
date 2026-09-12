"""Tests for application configuration."""

import pytest
from pydantic import ValidationError

from src.shared_kernel.config import LOGS_BACKEND_NONE, BaseAppSettings


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


def test_settings__logs_backend_none__logs_disabled():
    # arrange
    settings = BaseAppSettings(
        DJANGO_SECRET_KEY='test-key',
        LOGS_BACKEND=LOGS_BACKEND_NONE,
    )

    # act
    result = settings.logs_enabled

    # assert
    assert result is False


def test_settings__logs_backend_unknown__accepted_and_enabled():
    """The backend accepts any string there; this service only asks
    whether the pipeline is on, so a backend it never heard of must
    not stop it."""

    # arrange
    settings = BaseAppSettings(
        DJANGO_SECRET_KEY='test-key',
        LOGS_BACKEND='loki',
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
            LOGS_BACKEND='local',
            LOGS_REDIS_URL='http://redis:6379/4',
        )


def test_settings__logs_on_rediss_url__accepted():
    # arrange
    settings = BaseAppSettings(
        DJANGO_SECRET_KEY='test-key',
        LOGS_BACKEND='local',
        LOGS_REDIS_URL='rediss://:pw@redis:6380/4',
    )

    # act
    result = settings.LOGS_REDIS_URL

    # assert
    assert result == 'rediss://:pw@redis:6380/4'


def test_settings__logs_off_url_not_redis__accepted():
    """With the pipeline off the URL is never dialled, so it is not
    checked either: a stale value must not stop the service."""

    # arrange
    settings = BaseAppSettings(
        DJANGO_SECRET_KEY='test-key',
        LOGS_BACKEND=LOGS_BACKEND_NONE,
        LOGS_REDIS_URL='http://redis:6379/4',
    )

    # act
    result = settings.LOGS_REDIS_URL

    # assert
    assert result == 'http://redis:6379/4'
