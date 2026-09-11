import logging
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlsplit, urlunsplit

import requests
from django.conf import settings

from src.logs.events.exceptions import (
    SinkPermanentError,
    SinkTemporaryError,
)
from src.logs.events.reporting import report_error
from src.logs.events.schema import Event, dump_json
from src.logs.events.sinks.base import BaseSink
from src.logs.events.sinks.otlp_payload import build_otlp_payload
from src.utils.logging import SentryLogLevel

logger = logging.getLogger('pneumatic.events')

LOGS_PATH = '/v1/logs'
JSON_HEADERS = {'Content-Type': 'application/json'}
# Connect and read timeouts: a slow collector must not hold the tick.
DEFAULT_TIMEOUT = (3.05, 10.0)
RETRY_AFTER_HEADER = 'Retry-After'
# A longer pause than the whole retry sequence is not worth waiting.
MAX_RETRY_AFTER = 10
# The batch itself is wrong: a malformed body, a body too large, a
# wrong content type, an unprocessable record. Everything else, 401,
# 403, 404 and 405 included, is a misconfiguration of the endpoint or
# of the proxy in front of it and gets fixed without our help, so the
# records wait in the stream instead of going to the dead letter.
PERMANENT_STATUSES = (400, 413, 415, 422)
BODY_LIMIT = 500
PARTIAL_SUCCESS_KEY = 'partialSuccess'
REJECTED_RECORDS_KEY = 'rejectedLogRecords'


class OTLPSink(BaseSink):

    """ OTLP/HTTP JSON logs exporter: one POST per batch.

        The consumer sees only SinkTemporaryError (keep the batch
        pending and try again) or SinkPermanentError (dead letter);
        every transport detail stays in this class. """

    name = 'otlp'

    def __init__(
        self,
        endpoint: str,
        timeout: Tuple[float, float] = DEFAULT_TIMEOUT,
        session: Optional[requests.Session] = None,
    ):
        self.url = endpoint.rstrip('/') + LOGS_PATH
        self.display_url = without_userinfo(self.url)
        self.timeout = timeout
        # One session per sink, and one sink per endpoint per process
        # (get_sink): a session rebuilt every tick would open a new
        # connection for every batch it sends.
        self.session = session or requests.Session()

    def _send(self, records: List[Tuple[str, Event]]) -> None:
        payload = build_otlp_payload(
            records,
            service_name=settings.LOGS_SERVICE_NAME,
            service_version=settings.LOGS_SERVICE_VERSION,
            environment=settings.CONFIGURATION_CURRENT,
            observed_ns=time.time_ns(),
        )
        response = self.session.post(
            self.url,
            data=dump_json(payload).encode(),
            headers=JSON_HEADERS,
            timeout=self.timeout,
        )
        response.raise_for_status()
        self._report_rejected(response, len(records))

    def _handle_error(
        self,
        exc: Exception,
        records: List[Tuple[str, Event]],
    ) -> None:

        """ Only an answer that condemns this very batch is permanent
            (PERMANENT_STATUSES); network trouble and every other
            status are worth another try. An error that is not about
            the transport at all comes from building the batch: the
            records themselves are the problem, and sending them again
            would block the stream on the same batch forever, so they
            go to the dead letter for inspection. """

        if isinstance(exc, (requests.ConnectionError, requests.Timeout)):
            raise SinkTemporaryError(self._transport_message(exc)) from exc
        if not isinstance(exc, requests.RequestException):
            raise self._build_error(exc, len(records)) from exc
        response = exc.response
        status = response.status_code if response is not None else None
        if status is None:
            # Unknown transport failure: the batch stays pending.
            raise SinkTemporaryError(self._transport_message(exc)) from exc
        if status in PERMANENT_STATUSES:
            raise self._permanent_error(
                exc.response, status, len(records),
            ) from exc
        raise self._temporary_error(exc.response, status) from exc

    def _transport_message(self, exc: Exception) -> str:

        """ requests repeats the url it dialled, credential included,
            inside its own message: the repr is not to be trusted. """

        return f'{self.display_url}: {type(exc).__name__}'

    def _temporary_error(self, response, status: int) -> SinkTemporaryError:
        return SinkTemporaryError(
            f'{self.display_url} answered {status}',
            retry_after=self._retry_after(response),
        )

    def _permanent_error(
        self,
        response,
        status: int,
        count: int,
    ) -> SinkPermanentError:
        body = self._body_prefix(response)
        message = f'{self.display_url} answered {status} for {count} records'
        logger.error('%s: %s', message, body)
        report_error(
            message='OTLP endpoint rejected the batch',
            data={
                'url': self.display_url,
                'status': status,
                'records': count,
                'body': body,
            },
        )
        return SinkPermanentError(f'{message}: {body}')

    def _build_error(self, exc: Exception, count: int) -> SinkPermanentError:
        message = f'OTLP batch cannot be built ({count} records): {exc!r}'
        logger.error(message)
        report_error(
            message='OTLP batch cannot be built',
            data={'records': count, 'error': repr(exc)},
        )
        return SinkPermanentError(message)

    def _report_rejected(self, response, count: int) -> None:

        """ A 2xx with partialSuccess means the collector took the
            batch but dropped some records. Sending them again would
            change nothing, so the batch counts as delivered. The
            report is throttled: a collector that drops a record of
            every batch would otherwise cost a message per tick. """

        rejected = self._rejected_records(response)
        if not rejected:
            return
        logger.warning(
            'OTLP endpoint dropped records of a batch: %s of %s',
            rejected, count,
        )
        report_error(
            message='OTLP endpoint dropped records of a batch',
            data={
                'url': self.display_url,
                'rejected': rejected,
                'records': count,
            },
            level=SentryLogLevel.WARNING,
        )

    @staticmethod
    def _retry_after(response) -> Optional[float]:

        """ Honour the header only when it asks for a short pause:
            a longer one belongs to the next tick, not to this one.
            The HTTP date form is ignored on purpose. """

        try:
            delay = float(response.headers.get(RETRY_AFTER_HEADER))
        except (AttributeError, TypeError, ValueError):
            return None
        if 0 < delay <= MAX_RETRY_AFTER:
            return delay
        return None

    @staticmethod
    def _body_prefix(response) -> str:

        """ First bytes of the answer: enough to tell a schema error
            from a wrong path, short enough for Sentry. """

        try:
            return response.content[:BODY_LIMIT].decode(
                'utf-8', errors='replace',
            )
        except (AttributeError, TypeError, ValueError):
            return ''

    @staticmethod
    def _rejected_records(response) -> int:
        try:
            body = response.json()
        except ValueError:
            return 0
        if not isinstance(body, dict):
            return 0
        partial = body.get(PARTIAL_SUCCESS_KEY) or {}
        try:
            return int(partial.get(REJECTED_RECORDS_KEY) or 0)
        except (AttributeError, TypeError, ValueError):
            return 0


def without_userinfo(url: str) -> str:

    """ The url without the user:password part of its authority. """

    parts = urlsplit(url)
    if not parts.username and not parts.password:
        return url
    host = parts.hostname or ''
    if parts.port is not None:
        host = f'{host}:{parts.port}'
    return urlunsplit(parts._replace(netloc=host))


_sinks: Dict[str, OTLPSink] = {}


def get_sink() -> OTLPSink:

    """ Shared sink of the process: the keep alive connection of its
        session is reused between ticks. A settings change gives a new
        sink, exactly as get_stream() does for the stream. """

    endpoint = settings.LOGS_OTLP_ENDPOINT
    sink = _sinks.get(endpoint)
    if sink is None:
        sink = OTLPSink(endpoint)
        _sinks[endpoint] = sink
    return sink
