"""Tests for the HTTP context of a record."""

from src.shared_kernel.events.context import (
    USER_AGENT_MAX,
    get_client_ip,
    get_request_context,
    get_request_id,
    get_user_agent,
    resolve_request_id,
)
from src.shared_kernel.events.schema import RequestContext


def test_get_client_ip__x_real_ip__used(make_context_request):
    # arrange
    request = make_context_request(
        headers={'x-real-ip': ' 203.0.113.7 '},
        client_ip='10.0.0.1',
    )

    # act
    result = get_client_ip(request)

    # assert
    assert result == '203.0.113.7'


def test_get_client_ip__x_forwarded_for_only__ignored(make_context_request):
    # arrange
    request = make_context_request(
        headers={'x-forwarded-for': '203.0.113.7'},
        client_ip='10.0.0.1',
    )

    # act
    result = get_client_ip(request)

    # assert
    assert result == '10.0.0.1'


def test_get_client_ip__no_client__fallback(make_context_request):
    # arrange
    request = make_context_request(has_client=False)

    # act
    result = get_client_ip(request)

    # assert
    assert result == '0.0.0.0'


def test_get_user_agent__header__kept(make_context_request):
    # arrange
    request = make_context_request(headers={'user-agent': 'Mozilla/5.0'})

    # act
    result = get_user_agent(request)

    # assert
    assert result == 'Mozilla/5.0'


def test_get_user_agent__no_header__none(make_context_request):
    # arrange
    request = make_context_request()

    # act
    result = get_user_agent(request)

    # assert
    assert result is None


def test_get_user_agent__long_header__cut(make_context_request):
    # arrange
    request = make_context_request(
        headers={'user-agent': 'a' * (USER_AGENT_MAX + 1)},
    )

    # act
    result = get_user_agent(request)

    # assert
    assert result == 'a' * USER_AGENT_MAX


def test_resolve_request_id__safe_value__kept():
    # act
    result = resolve_request_id('req-1.2_3~4+5/6=7')

    # assert
    assert result == 'req-1.2_3~4+5/6=7'


def test_resolve_request_id__none__fresh_hex():
    # act
    result = resolve_request_id(None)

    # assert
    assert len(result) == 32
    assert int(result, 16) >= 0


def test_resolve_request_id__too_long__replaced():
    # arrange
    value = 'a' * 65

    # act
    result = resolve_request_id(value)

    # assert
    assert result != value
    assert len(result) == 32


def test_resolve_request_id__unsafe_chars__replaced():
    # arrange
    value = 'req 1\nnext'

    # act
    result = resolve_request_id(value)

    # assert
    assert result != value
    assert len(result) == 32


def test_get_request_id__stored_by_middleware__returned(
    make_context_request,
):
    # arrange
    request = make_context_request(
        headers={'x-request-id': 'from-header'},
        request_id='from-state',
    )

    # act
    result = get_request_id(request)

    # assert
    assert result == 'from-state'


def test_get_request_id__no_middleware__from_header(make_context_request):
    # arrange
    request = make_context_request(headers={'x-request-id': 'from-header'})

    # act
    result = get_request_id(request)

    # assert
    assert result == 'from-header'


def test_get_request_id__nothing__fresh_hex(make_context_request):
    # arrange
    request = make_context_request()

    # act
    result = get_request_id(request)

    # assert
    assert len(result) == 32


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
