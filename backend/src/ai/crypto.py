import base64
import hashlib
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings

# Prefix marking values encrypted by this module; anything without it
# is treated as legacy plaintext (pre-encryption rows)
ENCRYPTED_PREFIX = 'fernet:'


def _fernet() -> Fernet:

    """ AI_ENCRYPTION_KEY (a urlsafe-base64 32-byte Fernet key) wins;
        without it the key is derived from SECRET_KEY so encryption
        works out of the box. Rotating SECRET_KEY then invalidates
        stored provider keys — owners re-enter them """

    key = getattr(settings, 'AI_ENCRYPTION_KEY', None)
    if key:
        return Fernet(key)
    derived = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(derived))


def encrypt_api_key(value: Optional[str]) -> Optional[str]:
    if not value:
        return value
    if value.startswith(ENCRYPTED_PREFIX):
        return value
    token = _fernet().encrypt(value.encode()).decode()
    return f'{ENCRYPTED_PREFIX}{token}'


def decrypt_api_key(value: Optional[str]) -> Optional[str]:
    if not value or not value.startswith(ENCRYPTED_PREFIX):
        return value
    token = value[len(ENCRYPTED_PREFIX):]
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken:
        # the encryption key changed since this row was written; the
        # stored key is unrecoverable — behave like a missing key so
        # the owner re-enters it
        return ''
