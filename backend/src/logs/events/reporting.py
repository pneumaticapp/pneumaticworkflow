from time import monotonic
from typing import Any, Dict

from src.utils.logging import SentryLogLevel, capture_sentry_message

REPORT_INTERVAL = 60
_last_reports: Dict[str, float] = {}


def report_error(
    message: str,
    data: Dict[str, Any],
    level: str = SentryLogLevel.ERROR,
) -> None:

    """ Send a message to Sentry, at most once per REPORT_INTERVAL for
        the same message. Callers keep their own log line: the log is
        cheap and shows every occurrence. """

    now = monotonic()
    last_report = _last_reports.get(message)
    if last_report is not None and now - last_report < REPORT_INTERVAL:
        return
    _last_reports[message] = now
    capture_sentry_message(
        message=message,
        data=data,
        level=level,
    )
