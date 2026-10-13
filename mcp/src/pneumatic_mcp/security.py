"""Defense in depth for SDK/server logs, including validation failures."""

import logging
import re

URL = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
OPAQUE = re.compile(
    r"\b(?:mcp-[dut]_[A-Za-z0-9_-]+|[A-Za-z0-9_~+/-]{24,}=*)\b"
)
BEARER = re.compile(r"(?i)Bearer\s+[^\s,\"']+")


class RedactingFilter(logging.Filter):
    def __init__(self, secret: str):
        super().__init__()
        self.secret = secret

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        if self.secret:
            message = message.replace(self.secret, "[REDACTED]")
        message = URL.sub("[URL REDACTED]", message)
        message = BEARER.sub("Bearer [REDACTED]", message)
        record.msg = OPAQUE.sub("[REDACTED]", message)
        record.args = ()
        # SDK validation tracebacks may contain the complete request/result
        # body.
        record.exc_info = None
        record.exc_text = None
        return True


def configure_redaction(secret: str):
    for logger in (
        logging.getLogger(),
        logging.getLogger("uvicorn.error"),
        logging.getLogger("uvicorn.access"),
        logging.getLogger("uvicorn"),
    ):
        for handler in logger.handlers:
            if not any(
                isinstance(item, RedactingFilter) for item in handler.filters
            ):
                handler.addFilter(RedactingFilter(secret))
