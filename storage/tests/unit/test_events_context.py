"""Tests for the HTTP context of a record."""

from src.shared_kernel.events.context import get_request_context
from src.shared_kernel.events.schema import RequestContext


def test_get_request_context__request__assembled(make_context_request):
    # arrange
    request = make_context_request(
        headers={'x-real-ip': '203.0.113.7', 'user-agent': 'Mozilla/5.0'},
        request_id='req-1',
    )

    # act
    result = get_request_context(request)

    # assert
    assert result == RequestContext(
        ip='203.0.113.7',
        user_agent='Mozilla/5.0',
        request_id='req-1',
    )
