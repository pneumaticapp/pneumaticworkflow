"""Canonical filenames shared by browser uploads and URL imports."""

import re

_RE_UNSAFE_CHARS = re.compile(r'[^\w.\- ]', re.UNICODE)
_RE_WHITESPACE = re.compile(r'[\s_]+')
FALLBACK_FILENAME = 'unnamed_file'


def secure_filename(filename: str | None) -> str:
    """Sanitize filename to prevent path traversal and unsafe characters.

    Preserves Unicode letters (Cyrillic, CJK, etc.) while blocking
    control characters, path separators, and shell metacharacters.
    """
    if not filename:
        return FALLBACK_FILENAME
    # Keep Unicode word chars (\w), dot, dash, space
    filename = _RE_UNSAFE_CHARS.sub('_', filename)
    # Collapse multiple spaces/underscores
    filename = _RE_WHITESPACE.sub('_', filename)
    # Prevent hidden files and traversal
    filename = filename.lstrip('._')
    # Strip trailing dots/spaces (Windows FS issue)
    filename = filename.rstrip('. ')
    if not filename:
        return FALLBACK_FILENAME
    return filename
