"""Fixtures of the event pipeline: the resets of its process
globals and the in memory stream. An app whose tests read the
events back imports them in its tests/conftest.py, and the
resets come along with the stream: they are autouse there."""

from types import SimpleNamespace

import pytest
from django.test import RequestFactory

from src.logs.enums import LogsBackend
from src.logs.events import sink as sink_module
from src.logs.events import stream as stream_module
from src.logs.events.services import AuditEventService
from src.logs.events.tests.fixtures import FakeEventStream
from src.utils import logging as sentry_logging


@pytest.fixture(autouse=True)
def reset_error_throttle():
    """capture_sentry_message_throttled keeps its last moment per key
    in a process global, so without this one test would silence the
    next."""
    sentry_logging._sentry_last_messages.clear()


@pytest.fixture(autouse=True)
def reset_stream_circuit():
    """A failed write in one test must not silence the next."""
    AuditEventService._circuit_open_until = 0.0
    AuditEventService._dropped = 0


@pytest.fixture(autouse=True)
def reset_stream_cache():
    """get_stream() keeps one client per settings tuple in a process
    global, so a client built with the settings of one test would
    be handed to the next one."""
    stream_module._streams.clear()


@pytest.fixture(autouse=True)
def reset_sink_cache():
    """get_sink() keeps one session per endpoint, same reason."""
    sink_module._sinks.clear()


@pytest.fixture
def events_enabled(settings):
    """Turn the pipeline on: the test settings leave LOGS_BACKEND
    unset, and the enabled pipeline requires every setting it
    needs, so all of them are filled in. Nothing is ever
    dialled: a test that writes swaps the stream for the in memory
    one, a test of the consumer swaps the stream and the sink."""
    settings.LOGS_BACKEND = LogsBackend.OTLP
    settings.LOGS_REDIS_URL = 'redis://localhost:6379/4'
    settings.LOGS_STREAM_MAXLEN = 1000000
    settings.LOGS_OTLP_ENDPOINT = 'http://otel-collector:4318'
    settings.LOGS_CONSUMER_BATCH_SIZE = 1000
    return settings


@pytest.fixture
def run_on_commit(mocker):
    """pytest-django keeps the transaction open, so on_commit
    callbacks never run. Write straight away instead.

    Only the service transaction reference is replaced, so its real
    writer runs. Deferral is covered by test_pipeline. Patching
    django.db.transaction.on_commit would change the behaviour of
    every other caller in the project for the whole test."""
    mocker.patch(
        'src.logs.events.services.transaction',
        new=SimpleNamespace(on_commit=lambda callback: callback()),
    )


@pytest.fixture
def scheduled_stream(mocker, events_enabled):
    """In memory stream instead of Redis, with the pipeline on and
    the writes still deferred to the commit: for the tests of the
    deferral itself.

    The patch of get_stream is not asserted: it is the environment
    of every test that takes the fixture, and what an action wrote
    is read back from the stream itself."""
    stream = FakeEventStream()
    mocker.patch('src.logs.events.services.get_stream', return_value=stream)
    return stream


@pytest.fixture
def fake_stream(scheduled_stream, run_on_commit):
    """The same stream with the writes immediate: what a test needs
    to read back the event an action published. A test of the
    pipeline being off sets LOGS_BACKEND back to None itself."""
    return scheduled_stream


@pytest.fixture
def request_factory():
    return RequestFactory()
