from time import monotonic
from typing import Any, Dict, Optional

from src.utils.logging import SentryLogLevel, capture_sentry_message

REPORT_INTERVAL = 60
_last_reports: Dict[str, float] = {}


def report_error(
    message: str,
    data: Dict[str, Any],
    level: str = SentryLogLevel.ERROR,
    key: Optional[str] = None,
) -> None:

    """ Send a message to Sentry, at most once per REPORT_INTERVAL for
        the same key. Callers keep their own log line: the log is
        cheap and shows every occurrence.

        key tells apart occurrences that share a message but not a
        cause, an unknown event type per name above all; it defaults
        to the message, which is one bucket for everything. """

    now = monotonic()
    throttle_key = key or message
    last_report = _last_reports.get(throttle_key)
    if last_report is not None and now - last_report < REPORT_INTERVAL:
        return
    _last_reports[throttle_key] = now
    capture_sentry_message(
        message=message,
        data=data,
        level=level,
    )
