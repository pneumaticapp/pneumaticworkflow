"""Remove bearer capabilities and URL queries from logs and telemetry."""

import logging
import re
from typing import Any

_TICKETS = re.compile(r'(/mcp/download/)[^\s/?\"\'<>]+')
_URL_QUERIES = re.compile(r'((?:https?://|/)[^\s?\"\'<>]+)\?[^\s\"\'<>]*')
_CREDENTIALS = re.compile(r'mcp-[du]_[A-Za-z0-9_-]+')
_SECRET_KEYS = frozenset(
    {
        'authorization',
        'cookie',
        'set-cookie',
        'x-mcp-delegation',
        'credential',
        'ticket',
        'access_token',
        'refresh_token',
        'query_string',
    }
)


def redact_text(value: str) -> str:
    """Redact request-target tickets and all URL query strings."""
    value = _TICKETS.sub(r'\1[redacted]', value)
    value = _URL_QUERIES.sub(r'\1?[redacted]', value)
    return _CREDENTIALS.sub('[redacted]', value)


def redact_data(value: Any) -> Any:  # noqa: ANN401, PLR0911
    """Sanitize nested telemetry including headers, breadcrumbs and spans."""
    if isinstance(value, dict):
        if value.get('loc') and str(value['loc'][-1]).lower() in _SECRET_KEYS:
            value = {**value, 'input': '[redacted]'}
        return {
            key: '[redacted]'
            if str(key).lower() in _SECRET_KEYS
            else redact_data(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        # Sentry also represents headers as name/value pairs.
        if len(value) == 2 and str(value[0]).lower() in _SECRET_KEYS:  # noqa: PLR2004
            return [value[0], '[redacted]']
        return [redact_data(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_data(item) for item in value)
    if isinstance(value, str):
        return redact_text(value)
    return value


class RedactionFilter(logging.Filter):
    """Filter formatted records before access or HTTP logs are emitted."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Keep every record, replacing only sensitive text."""
        # Uvicorn's AccessFormatter consumes the five original arguments.
        # Preserve their shape and numeric status while sanitizing strings.
        record.msg = redact_text(str(record.msg))
        record.args = redact_data(record.args)
        if record.name != 'uvicorn.access':
            record.msg = redact_text(record.getMessage())
            record.args = ()
        for key in ('request_path', 'details'):
            if key in record.__dict__:
                record.__dict__[key] = redact_data(record.__dict__[key])
        return True


def install_log_redaction() -> None:
    """Cover Uvicorn access and all HTTP client transport loggers."""
    for name in (
        'uvicorn.access',
        'httpx',
        'httpcore',
        'httpcore.connection',
        'httpcore.http11',
        'httpcore.http2',
        'src.shared_kernel.exceptions.exception_handler',
    ):
        logging.getLogger(name).addFilter(RedactionFilter())
