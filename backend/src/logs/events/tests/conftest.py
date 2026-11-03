# ruff: noqa: F401
from unittest.mock import Mock

import guardian.management
import pytest

from src.authentication.enums import AuthTokenType
from src.generics.tests.clients import PneumaticApiClient
from src.logs.events.entities import RequestContext
from src.logs.events.entities import request_context as current_request_context
from src.logs.events.enums import EventCategory, UserEvents
from src.logs.events.tests.plugin import (
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
from src.processes.tests.fixtures import create_test_account, create_test_owner


def pytest_configure(config):
    guardian.management.create_anonymous_user = Mock()


@pytest.fixture
def api_client():
    return PneumaticApiClient(HTTP_USER_AGENT='Mozilla/5.0')


@pytest.fixture
def request_context():
    """Context of an HTTP request, as the middleware publishes it."""
    token = current_request_context.set(
        RequestContext(
            request_id='ctx-request',
            ip='9.9.9.9',
            user_agent='Chrome',
        ),
    )
    yield
    current_request_context.reset(token)


@pytest.fixture
def event_kwargs():
    """A real actor and a separate tenant selected by the caller."""
    user = create_test_owner(email='actor@test.test')
    account = create_test_account(name='Operations')
    return {
        'event_category': EventCategory.USERS,
        'event_type': UserEvents.LOGIN,
        'user': user,
        'auth_type': AuthTokenType.USER,
        'object_id': user.id,
        'object_name': user.email,
        'account_id': account.id,
        'account_name': account.name,
        'payload': {'source': 'email', 'password': 'sensitive'},
    }
