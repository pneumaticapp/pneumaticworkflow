from unittest.mock import Mock

import guardian.management
import pytest

from src.generics.tests.clients import PneumaticApiClient
from src.logs.events.context import (
    RequestContext,
    reset_context,
    set_context,
)
from src.logs.events.enums import ActorType
from src.logs.events.schema import Actor
from src.logs.events.tests.plugin import (  # noqa: F401
    events_enabled,
    fake_stream,
    request_factory,
    reset_error_throttle,
    reset_sink_cache,
    reset_stream_cache,
    reset_stream_circuit,
    run_on_commit,
    scheduled_stream,
)


def pytest_configure(config):
    guardian.management.create_anonymous_user = Mock()


@pytest.fixture
def api_client():
    return PneumaticApiClient(HTTP_USER_AGENT='Mozilla/5.0')


@pytest.fixture
def request_context():

    """ Context of an HTTP request, as the middleware publishes it. """

    token = set_context(
        RequestContext(
            request_id='ctx-request',
            ip='9.9.9.9',
            user_agent='Chrome',
            actor=Actor(
                type=ActorType.USER,
                id=77,
                email='ctx@test.test',
            ),
        ),
    )
    yield
    reset_context(token)
