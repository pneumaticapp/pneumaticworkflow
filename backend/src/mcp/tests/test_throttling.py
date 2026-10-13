from types import SimpleNamespace

import pytest
from django.http import HttpResponse
from django.test import RequestFactory
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from src.authentication.middleware import OAuthThrottleMiddleware
from src.authentication.throttling import OAuthRegisterThrottle


def test_oauth_throttle__interval_elapsed__request_admitted(
    oauth_rate: SimpleNamespace,
):
    # arrange
    request = RequestFactory().post(
        '/oauth/mcp/register',
        REMOTE_ADDR=oauth_rate.ip,
    )
    middleware = OAuthThrottleMiddleware(
        get_response=lambda request: HttpResponse(status=204),
    )

    # act
    first = middleware(request)
    blocked = middleware(request)
    oauth_rate.timer.return_value = 1061
    admitted = middleware(request)

    # assert
    assert first.status_code == 204
    assert blocked.status_code == 429
    assert blocked['Retry-After'] == '60'
    assert admitted.status_code == 204
    assert oauth_rate.backend.get(oauth_rate.keys['register']) == 1061


def test_oauth_throttle__different_ip_and_scope__independent_intervals(
    oauth_rate: SimpleNamespace,
):
    # arrange
    factory = RequestFactory()
    middleware = OAuthThrottleMiddleware(
        get_response=lambda request: HttpResponse(status=204),
    )
    register = factory.post('/oauth/mcp/register', REMOTE_ADDR=oauth_rate.ip)

    # act
    first = middleware(register)
    same_ip = middleware(register)
    other_ip = middleware(
        factory.post(
            '/oauth/mcp/register',
            REMOTE_ADDR='192.0.2.32',
        ),
    )
    other_scope = middleware(
        factory.post(
            '/oauth/mcp/token',
            REMOTE_ADDR=oauth_rate.ip,
        ),
    )

    # assert
    assert first.status_code == 204
    assert same_ip.status_code == 429
    assert other_ip.status_code == 204
    assert other_scope.status_code == 204


@pytest.mark.parametrize(
    'enabled,path,method,rate',
    [
        (False, '/oauth/mcp/register', 'post', '1/min'),
        (True, '/templates', 'post', '1/min'),
        (True, '/oauth/mcp/register', 'get', '1/min'),
        (True, '/oauth/mcp/register', 'post', None),
    ],
)
def test_oauth_throttle__not_applicable__no_cache_access(
    oauth_rate: SimpleNamespace,
    mcp_settings: SettingsWrapper,
    mocker: MockerFixture,
    enabled: bool,
    path: str,
    method: str,
    rate: str | None,
):
    # arrange
    mcp_settings.MCP_ENABLED = enabled
    oauth_rate.rates[OAuthRegisterThrottle.scope] = rate
    get = mocker.spy(oauth_rate.backend, 'get')
    request = getattr(RequestFactory(), method)(
        path,
        REMOTE_ADDR=oauth_rate.ip,
    )
    middleware = OAuthThrottleMiddleware(
        get_response=lambda request: HttpResponse(status=204),
    )

    # act
    response = middleware(request)

    # assert
    assert response.status_code == 204
    get.assert_not_called()
