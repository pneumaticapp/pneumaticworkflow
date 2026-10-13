from urllib.parse import urlparse

from rest_framework.exceptions import ValidationError

from src.storage.messages import MSG_FS_0021


def validate_import_url(value: str) -> str:
    """Validate syntax; storage checks public DNS/IPs before downloading."""
    try:
        parsed = urlparse(value)
        port = parsed.port
    except ValueError as ex:
        raise ValidationError(MSG_FS_0021) from ex
    if (
        parsed.scheme != 'https'
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.fragment
        or port not in (None, 443)
    ):
        raise ValidationError(MSG_FS_0021)
    return value
