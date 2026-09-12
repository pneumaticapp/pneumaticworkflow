import pytest

from src.generics.tests.clients import PneumaticApiClient
from src.logs.events.tests.plugin import (  # noqa: F401
    events_enabled,
    fake_stream,
    reset_error_throttle,
    reset_sink_cache,
    reset_stream_cache,
    reset_stream_circuit,
    run_on_commit,
    scheduled_stream,
)


@pytest.fixture
def api_client():
    return PneumaticApiClient(HTTP_USER_AGENT='Mozilla/5.0')


@pytest.fixture
def analysis_mock(mocker):
    return mocker.patch(
        'src.processes.views.workflow.AnalyticService',
    )
