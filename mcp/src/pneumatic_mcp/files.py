"""Canonical single-segment paths for migrated logical file IDs."""

import unicodedata
from urllib.parse import quote, unquote


def file_id_segment(value: object) -> str:
    # File IDs are storage identities, not display names. Preserve their exact
    # spelling, including Unicode and spaces, while rejecting path ambiguity.
    if (
        not isinstance(value, str)
        or not 1 <= len(value) <= 512
        or not value.strip()
        or value in {".", ".."}
        or any(
            char in "/\\?#%"
            or unicodedata.category(char).startswith("C")
            or unicodedata.category(char) in {"Zl", "Zp"}
            for char in value
        )
    ):
        raise ValueError("Expected a safe flat file ID")
    return quote(string=value, safe="")


def validate_file_path(path: str):
    prefix = "/mcp/files/"
    if not path.startswith(prefix):
        raise ValueError("Expected a delegated file API path")
    segment = path[len(prefix) :]
    if segment.endswith("/download-ticket"):
        segment = segment.removesuffix("/download-ticket")
    if file_id_segment(value=unquote(segment, errors="strict")) != segment:
        raise ValueError("Expected a canonical encoded file path")
