"""Tests for application configuration."""

import pytest
from pydantic import ValidationError

from src.shared_kernel.config import Settings


def test_settings__no_secret_key__raise_error(monkeypatch):

    # arrange
    monkeypatch.delenv('DJANGO_SECRET_KEY', raising=False)

    # act
    with pytest.raises(
        ValidationError, match='DJANGO_SECRET_KEY',
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
