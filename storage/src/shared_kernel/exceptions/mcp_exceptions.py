"""Sanitized operational failures at the trusted core boundary."""

# Project convention omits return annotations on procedures.
# mypy: disable-error-code="no-untyped-def"

from .base_exceptions import BaseAppError
from .error_codes import MCP_ERROR_CODES


class MCPCoreUnavailableError(BaseAppError):
    """Core cannot currently authorize or reconcile a file operation."""

    def __init__(self):  # noqa: ANN204
        """Avoid upstream URLs, credentials and exception text."""
        super().__init__(
            error_code=MCP_ERROR_CODES['CORE_UNAVAILABLE'],
        )


class MCPUploadConflictError(BaseAppError):
    """Core has already completed the session with different metadata."""

    def __init__(self):  # noqa: ANN204
        """Return a safe, actionable conflict."""
        super().__init__(
            error_code=MCP_ERROR_CODES['UPLOAD_CONFLICT'],
        )


class MCPImportError(BaseAppError):
    """An external URL cannot be imported safely."""

    def __init__(self):  # noqa: ANN204
        """Use the standard envelope without leaking the source URL."""
        super().__init__(error_code=MCP_ERROR_CODES['UNSAFE_IMPORT'])
