"""Content-Type sanitization for XSS prevention."""

# Safe MIME types whitelist.
# Any type not in this set will be replaced with
# application/octet-stream to prevent XSS via browser rendering.
ALLOWED_CONTENT_TYPES: frozenset[str] = frozenset({
    # Images
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
    'image/bmp',
    'image/tiff',
    'image/x-icon',
    'image/vnd.microsoft.icon',
    # Documents
    'application/pdf',
    'application/zip',
    'application/x-zip-compressed',
    'application/gzip',
    'application/x-tar',
    'application/x-7z-compressed',
    'application/x-rar-compressed',
    # Office
    'application/msword',
    'application/vnd.ms-excel',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument'
    '.wordprocessingml.document',
    'application/vnd.openxmlformats-officedocument'
    '.spreadsheetml.sheet',
    'application/vnd.openxmlformats-officedocument'
    '.presentationml.presentation',
    'application/vnd.oasis.opendocument.text',
    'application/vnd.oasis.opendocument.spreadsheet',
    # Text (safe, non-renderable as HTML)
    'text/plain',
    'text/csv',
    'text/tab-separated-values',
    # Audio
    'audio/mpeg',
    'audio/wav',
    'audio/ogg',
    'audio/webm',
    'audio/aac',
    'audio/flac',
    # Video
    'video/mp4',
    'video/webm',
    'video/ogg',
    'video/quicktime',
    'video/x-msvideo',
    # Data
    'application/json',
    'application/xml',
    'application/octet-stream',
})

# Dangerous types that can execute scripts in browser.
# Explicitly blocked even if added to ALLOWED_CONTENT_TYPES.
_BLOCKED_TYPES: frozenset[str] = frozenset({
    'text/html',
    'text/xml',
    'application/xhtml+xml',
    'application/javascript',
    'application/x-javascript',
    'text/javascript',
    'image/svg+xml',
    'application/ecmascript',
    'text/ecmascript',
})

_DEFAULT_SAFE_TYPE = 'application/octet-stream'


def sanitize_content_type(
    content_type: str | None,
) -> str:
    """Sanitize Content-Type to prevent stored XSS.

    Args:
        content_type: Raw Content-Type from client.

    Returns:
        Safe Content-Type string.

    """
    if not content_type:
        return _DEFAULT_SAFE_TYPE

    # Extract base type without parameters (charset, boundary)
    base_type = content_type.split(';')[0].strip().lower()

    if base_type in _BLOCKED_TYPES:
        return _DEFAULT_SAFE_TYPE

    if base_type in ALLOWED_CONTENT_TYPES:
        return base_type

    return _DEFAULT_SAFE_TYPE
