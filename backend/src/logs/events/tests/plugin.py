""" Fixtures of the event pipeline: the resets of its process
    globals and the in memory stream. An app whose tests read the
    events back imports them in its tests/conftest.py, and the
    resets come along with the stream: they are autouse there. """

import pytest
from django.test import RequestFactory

from src.logs.enums import LogsBackend
from src.logs.events import reporting
from src.logs.events import stream as stream_module
from src.logs.events.emitter import _write, reset_circuit
from src.logs.events.sinks import otlp as otlp_sink
from src.logs.events.tests.fakes import FakeEventStream


@pytest.fixture(autouse=True)
def reset_error_throttle():

    """ report_error keeps its last moment per key in a process
        global, so without this one test would silence the next.
        Unknown event types are throttled through the same table. """

    reporting._last_reports.clear()


@pytest.fixture(autouse=True)
def reset_stream_circuit():

    """ A failed write in one test must not silence the next. """

    reset_circuit()


@pytest.fixture(autouse=True)
def reset_stream_cache():

    """ get_stream() keeps one client per settings tuple in a process
        global, so a client built with the settings of one test would
        be handed to the next one. """

    stream_module._streams.clear()


@pytest.fixture(autouse=True)
def reset_sink_cache():

    """ get_sink() keeps one session per endpoint, same reason. """

    otlp_sink._sinks.clear()


@pytest.fixture
def events_enabled(settings):

    """ Turn the pipeline on: tests run with LOGS_BACKEND='none'. """

    settings.LOGS_BACKEND = LogsBackend.LOCAL
    return settings


@pytest.fixture
def run_on_commit(mocker):

    """ pytest-django keeps the transaction open, so on_commit
        callbacks never run. Write straight away instead.

        Only the scheduler of the emitter is replaced, and by the real
        writer rather than by a mock: there is nothing to assert about
        the deferral here, it is covered by test_emitter. Patching
        django.db.transaction.on_commit would change the behaviour of
        every other caller in the project for the whole test. """

    mocker.patch('src.logs.events.emitter._schedule', new=_write)


@pytest.fixture
def scheduled_stream(mocker, events_enabled):

    """ In memory stream instead of Redis, with the pipeline on and
        the writes still deferred to the commit: for the tests of the
        deferral itself. """

    stream = FakeEventStream()
    mocker.patch(
        'src.logs.events.emitter.get_stream',
        return_value=stream,
    )
    return stream


@pytest.fixture
def fake_stream(scheduled_stream, run_on_commit):

    """ The same stream with the writes immediate: what a test needs
        to read back the event an action published. A test of the
        pipeline being off sets LOGS_BACKEND back to none itself. """

    return scheduled_stream


@pytest.fixture
def request_factory():
    return RequestFactory()
