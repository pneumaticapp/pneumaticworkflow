"""Tests for what a request says about its client."""

import re

from src.shared_kernel.http_context import (
    USER_AGENT_MAX,
    get_client_ip,
    get_request_id,
    get_user_agent,
    resolve_request_id,
)


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
    assert re.fullmatch(r'[0-9a-f]{32}', result)


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


def test_get_request_id__middleware_ran__id_of_the_request(
    make_context_request,
):
    """One source and no fallback: the id of a record is the id the
    caller got back in the X-Request-ID header of the response."""

    # arrange
    request = make_context_request(request_id='req-1')

    # act
    result = get_request_id(request)

    # assert
    assert result == 'req-1'


def test_get_client_ip__x_real_ip_is_not_an_address__fallback(
    make_context_request,
):
    """Client controlled behind somebody else's balancer: a value
    that is not an address would ride in every record of the request
    and in the key of the rate limit bucket.
    """
    # arrange
    request = make_context_request(
        headers={'x-real-ip': 'not-an-address'},
        client_ip='10.0.0.1',
    )

    # act
    result = get_client_ip(request)

    # assert
    assert result == '10.0.0.1'
