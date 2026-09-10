from unittest.mock import Mock

import guardian.management
import pytest
from django.test import RequestFactory

from src.generics.tests.clients import PneumaticApiClient
from src.logs.events import reporting
from src.logs.events.context import (
    RequestContext,
    reset_context,
    set_context,
)
from src.logs.enums import LogsBackend
from src.logs.events.emitter import _write, reset_circuit
from src.logs.events.enums import ActorType
from src.logs.events.tests.fakes import FakeEventStream

CONTEXT_ACCOUNT_ID = 5


def pytest_configure(config):
    guardian.management.create_anonymous_user = Mock()


@pytest.fixture
def api_client():
    return PneumaticApiClient(HTTP_USER_AGENT='Mozilla/5.0')


@pytest.fixture(autouse=True)
def reset_error_throttle():

    """ report_error keeps its last moment per message in a process
        global, so without this one test would silence the next. """

    reporting._last_reports.clear()


@pytest.fixture(autouse=True)
def reset_stream_circuit():

    """ A failed write in one test must not silence the next. """

    reset_circuit()


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
def fake_stream(mocker):

    """ In memory stream instead of Redis for emit() and consumer. """

    stream = FakeEventStream()
    mocker.patch(
        'src.logs.events.emitter.get_stream',
        return_value=stream,
    )
    return stream


@pytest.fixture
def request_context():

    """ Context of an HTTP request, as the middleware publishes it. """

    token = set_context(
        RequestContext(
            request_id='ctx-request',
            ip='9.9.9.9',
            user_agent='Chrome',
            actor_type=ActorType.USER,
            actor_id=77,
            actor_email='ctx@test.test',
            account_id=CONTEXT_ACCOUNT_ID,
        ),
    )
    yield
    reset_context(token)


@pytest.fixture
def request_factory():
    return RequestFactory()
