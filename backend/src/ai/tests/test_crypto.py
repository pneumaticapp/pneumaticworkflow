import pytest
from cryptography.fernet import Fernet
from django.test import override_settings

from src.ai.crypto import (
    ENCRYPTED_PREFIX,
    decrypt_api_key,
    encrypt_api_key,
)
from src.ai.models import AIProviderConnection
from src.ai.providers import resolve_provider
from src.processes.tests.fixtures import create_test_user

pytestmark = pytest.mark.django_db

SECRET = 'sk-or-v1-0123456789abcdef'


def test_encrypt__roundtrip__plaintext_recovered():
    encrypted = encrypt_api_key(SECRET)

    assert encrypted.startswith(ENCRYPTED_PREFIX)
    assert SECRET not in encrypted
    assert decrypt_api_key(encrypted) == SECRET


def test_encrypt__already_encrypted__unchanged():
    encrypted = encrypt_api_key(SECRET)

    assert encrypt_api_key(encrypted) == encrypted


def test_encrypt__empty_values__passthrough():
    assert encrypt_api_key('') == ''
    assert encrypt_api_key(None) is None


def test_decrypt__legacy_plaintext__passthrough():
    assert decrypt_api_key(SECRET) == SECRET
    assert decrypt_api_key('') == ''
    assert decrypt_api_key(None) is None


def test_decrypt__key_rotated__empty_string():
    encrypted = encrypt_api_key(SECRET)

    with override_settings(
        AI_ENCRYPTION_KEY=Fernet.generate_key().decode(),
    ):
        assert decrypt_api_key(encrypted) == ''


def test_decrypt__explicit_encryption_key__roundtrip():
    with override_settings(
        AI_ENCRYPTION_KEY=Fernet.generate_key().decode(),
    ):
        encrypted = encrypt_api_key(SECRET)

        assert decrypt_api_key(encrypted) == SECRET


def test_connection__api_key_property__column_holds_ciphertext():
    user = create_test_user()

    connection = AIProviderConnection.objects.create(
        account=user.account,
        name='OpenRouter',
        api_key=SECRET,
    )

    connection.refresh_from_db()
    assert connection.api_key_encrypted.startswith(ENCRYPTED_PREFIX)
    assert SECRET not in connection.api_key_encrypted
    assert connection.api_key == SECRET


def test_connection__legacy_plaintext_row__still_readable():
    user = create_test_user()
    connection = AIProviderConnection.objects.create(
        account=user.account,
        name='OpenRouter',
    )
    # a pre-encryption row: plaintext straight in the column
    AIProviderConnection.objects.filter(id=connection.id).update(
        api_key_encrypted=SECRET,
    )

    connection.refresh_from_db()
    assert connection.api_key == SECRET


def test_resolve_provider__encrypted_connection__plaintext_key():
    user = create_test_user()
    AIProviderConnection.objects.create(
        account=user.account,
        name='OpenRouter',
        base_url='https://openrouter.ai/api/v1',
        api_key=SECRET,
    )

    _base_url, api_key = resolve_provider(user.account)

    assert api_key == SECRET
