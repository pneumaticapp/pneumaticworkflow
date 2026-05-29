"""Tests for application configuration."""

import pytest
from pydantic import ValidationError

from src.shared_kernel.config import Settings


def test_settings__no_secret_key__raise_error(monkeypatch):
    """Test Settings requires DJANGO_SECRET_KEY."""
    # arrange
    monkeypatch.delenv('DJANGO_SECRET_KEY', raising=False)

    # act
    with pytest.raises(ValidationError, match='DJANGO_SECRET_KEY'):

        # assert
        Settings(
            _env_file=None,
            DJANGO_SECRET_KEY=None,
        )


def test_settings__with_secret_key__ok():
    """Test Settings accepts explicit DJANGO_SECRET_KEY."""
    # act
    settings = Settings(
        DJANGO_SECRET_KEY='test-secret-key',
    )

    # assert
    assert settings.DJANGO_SECRET_KEY == 'test-secret-key'


def test_settings__cors_string__parsed_list():
    """Comma-separated CORS string parsed to list."""
    # act
    settings = Settings(
        DJANGO_SECRET_KEY='test-key',
        ALLOWED_ORIGINS='http://a.com,http://b.com',
    )

    # assert
    assert settings.ALLOWED_ORIGINS == [
        'http://a.com',
        'http://b.com',
    ]


def test_settings__cors_list__unchanged():
    """CORS list stays unchanged."""
    # act
    settings = Settings(
        DJANGO_SECRET_KEY='test-key',
        ALLOWED_ORIGINS=['http://a.com', 'http://b.com'],
    )

    # assert
    assert settings.ALLOWED_ORIGINS == [
        'http://a.com',
        'http://b.com',
    ]
