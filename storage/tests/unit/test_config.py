"""Tests for application configuration."""

import pytest
from pydantic import ValidationError

from src.shared_kernel.config import Settings


def test_settings__no_secret_key__raise_error(monkeypatch):
    # arrange
    monkeypatch.delenv('DJANGO_SECRET_KEY', raising=False)

    # act
    with pytest.raises(
        ValidationError,
        match='DJANGO_SECRET_KEY',
    ):
        Settings(_env_file=None)


def test_settings__with_secret_key__ok():
    # arrange
    settings = Settings(
        DJANGO_SECRET_KEY='test-secret-key',
    )

    # act
    result = settings.DJANGO_SECRET_KEY

    # assert
    assert result == 'test-secret-key'


def test_settings__cors_string__parsed_list():
    # arrange
    settings = Settings(
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
    settings = Settings(
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
    settings = Settings(
        DJANGO_SECRET_KEY='test-key',
        FASTAPI_BASE_URL='http://localhost:8000/',
        BACKEND_PRIVATE_URL='http://backend:8001/',
    )

    # act & assert
    assert settings.FASTAPI_BASE_URL == 'http://localhost:8000'
    assert settings.BACKEND_PRIVATE_URL == 'http://backend:8001'


def test_settings__no_trailing_slash__unchanged():
    # arrange
    settings = Settings(
        DJANGO_SECRET_KEY='test-key',
        FASTAPI_BASE_URL='http://localhost:8000',
    )

    # act
    result = settings.FASTAPI_BASE_URL

    # assert
    assert result == 'http://localhost:8000'


def test_settings__check_permission_url__no_double_slash():
    # arrange
    settings = Settings(
        DJANGO_SECRET_KEY='test-key',
        BACKEND_PRIVATE_URL='http://backend:8001/',
    )

    # act
    result = settings.check_permission_url

    # assert
    assert '//' not in result.replace('http://', '')


def test_settings__frontend_url__appended_to_cors():
    # arrange
    settings = Settings(
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
    settings = Settings(
        DJANGO_SECRET_KEY='test-key',
        ALLOWED_ORIGINS=['http://frontend.com'],
        FRONTEND_URL='http://frontend.com',
    )

    # act
    result = settings.ALLOWED_ORIGINS

    # assert
    assert result.count('http://frontend.com') == 1
