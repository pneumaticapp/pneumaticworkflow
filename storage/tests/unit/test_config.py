"""Tests for application configuration."""

import pytest
from pydantic import ValidationError

from src.shared_kernel.config import Settings


class TestSettings:
    """Test Settings validation."""

    def test_settings__no_secret_key__raise_error(
        self,
        monkeypatch,
    ):
        """Test Settings requires DJANGO_SECRET_KEY."""
        # arrange — ensure env var is unset
        monkeypatch.delenv('DJANGO_SECRET_KEY', raising=False)

        # act & assert
        with pytest.raises(ValidationError, match='DJANGO_SECRET_KEY'):
            Settings(
                _env_file=None,
                DJANGO_SECRET_KEY=None,
            )

    def test_settings__with_secret_key__ok(self):
        """Test Settings accepts explicit DJANGO_SECRET_KEY."""
        # act
        settings = Settings(
            DJANGO_SECRET_KEY='test-secret-key',
        )

        # assert
        assert settings.DJANGO_SECRET_KEY == 'test-secret-key'

    def test_settings__cors_string__parsed_list(self):
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

    def test_settings__cors_list__unchanged(self):
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
