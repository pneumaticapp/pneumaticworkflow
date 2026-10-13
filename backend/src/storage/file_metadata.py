import re
import unicodedata
from typing import Optional
from urllib.parse import quote, unquote_to_bytes

from src.storage import messages
from src.storage.constants import (
    BINARY_CONTENT_TYPE,
    MAX_FILE_ID_LENGTH,
    UNNAMED_FILE,
)


def valid_file_id(value: str) -> bool:
    return (
        isinstance(value, str)
        and 1 <= len(value) <= MAX_FILE_ID_LENGTH
        and not value.isspace()
        and value not in {'.', '..'}
        and not any(
            char in '/\\?#%'
            or unicodedata.category(char).startswith('C')
            or unicodedata.category(char) in {'Zl', 'Zp'}
            for char in value
        )
    )


def encoded_file_id(value: str) -> str:
    if not valid_file_id(value=value):
        raise ValueError(messages.MSG_FS_0012)
    return quote(value, safe='')


def decode_file_segment(value: str) -> Optional[str]:
    try:
        decoded = unquote_to_bytes(value).decode('utf-8')
        if encoded_file_id(value=decoded) != value:
            return None
    except (ValueError, UnicodeError):
        return None
    return decoded


# Keep this set aligned with storage.shared_kernel.security. Unsafe/unknown
# browser types are stored and served as binary, never browser executable MIME.
SAFE_CONTENT_TYPES = frozenset(
    {
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/webp',
        'image/bmp',
        'image/tiff',
        'image/x-icon',
        'image/vnd.microsoft.icon',
        'application/pdf',
        'application/zip',
        'application/x-zip-compressed',
        'application/gzip',
        'application/x-tar',
        'application/x-7z-compressed',
        'application/x-rar-compressed',
        'application/msword',
        'application/vnd.ms-excel',
        'application/vnd.ms-powerpoint',
        (
            'application/vnd.openxmlformats-officedocument.'
            'wordprocessingml.document'
        ),
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        (
            'application/vnd.openxmlformats-officedocument.'
            'presentationml.presentation'
        ),
        'application/vnd.oasis.opendocument.text',
        'application/vnd.oasis.opendocument.spreadsheet',
        'text/plain',
        'text/csv',
        'text/tab-separated-values',
        'audio/mpeg',
        'audio/wav',
        'audio/ogg',
        'audio/webm',
        'audio/aac',
        'audio/flac',
        'video/mp4',
        'video/webm',
        'video/ogg',
        'video/quicktime',
        'video/x-msvideo',
        'application/json',
        'application/xml',
        'application/octet-stream',
    },
)


def canonical_filename(value: str) -> str:
    value = re.sub(r'[^\w.\- ]', '_', value)
    value = re.sub(r'[\s_]+', '_', value)
    return value.lstrip('._').rstrip('. ') or UNNAMED_FILE


def canonical_content_type(value: str) -> str:
    value = value.split(';', maxsplit=1)[0].strip().lower()
    return value if value in SAFE_CONTENT_TYPES else BINARY_CONTENT_TYPE
