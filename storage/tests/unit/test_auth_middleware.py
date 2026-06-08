"""Tests for authentication middleware."""

import json
from unittest.mock import AsyncMock

import pytest

from src.shared_kernel.auth.user_types import UserType
from src.shared_kernel.middleware.auth_middleware import AuthUser


def test_auth_user__valid_data__ok():
    # act
    user = AuthUser(
        auth_type=UserType.AUTHENTICATED,
        user_id=1,
        account_id=2,
    )

    # assert
    assert user.user_id == 1
    assert user.account_id == 2
    assert user.is_anonymous is False


@pytest.mark.asyncio
async def test_authenticate_token__valid_token__return_user(
    auth_middleware,
    mocker,
):
    # arrange
    token = 'valid-token'
    token_data_mock = mocker.patch(
        'src.shared_kernel.middleware.auth_middleware.PneumaticToken.data',
        new_callable=AsyncMock,
        return_value={'user_id': 1, 'account_id': 2},
    )

    # act
    result = await auth_middleware.authenticate_token(token)

    # assert
    assert result is not None
    assert result.user_id == 1
    assert result.account_id == 2
    token_data_mock.assert_called_once_with(token)


@pytest.mark.asyncio
async def test_authenticate_token__invalid__return_none(
    auth_middleware,
    mocker,
):
    # arrange
    token = 'invalid-token'
    token_data_mock = mocker.patch(
        'src.shared_kernel.middleware.auth_middleware.PneumaticToken.data',
        new_callable=AsyncMock,
        return_value=None,
    )

    # act
    result = await auth_middleware.authenticate_token(token)

    # assert
    assert result is None
    token_data_mock.assert_called_once_with(token)


@pytest.mark.asyncio
async def test_authenticate_token__exception__return_none(
    auth_middleware,
    mocker,
):
    # arrange
    token = 'error-token'
    token_data_mock = mocker.patch(
        'src.shared_kernel.middleware.auth_middleware.PneumaticToken.data',
        new_callable=AsyncMock,
        side_effect=ValueError('Token error'),
    )

    # act
    result = await auth_middleware.authenticate_token(token)

    # assert
    assert result is None
    token_data_mock.assert_called_once_with(token)


@pytest.mark.asyncio
async def test_dispatch__valid_token__return_ok(
    auth_middleware,
    auth_mw_request,
    auth_mw_call_next,
    mocker,
):
    # arrange
    auth_mw_request.headers = {
        'Authorization': 'Bearer valid-token',
    }
    token_data_mock = mocker.patch(
        'src.shared_kernel.middleware.auth_middleware.PneumaticToken.data',
        new_callable=AsyncMock,
        return_value={'user_id': 1, 'account_id': 2},
    )

    # act
    response = await auth_middleware.dispatch(
        auth_mw_request,
        auth_mw_call_next,
    )

    # assert
    assert response.status_code == 200
    assert auth_mw_request.state.user.user_id == 1
    assert auth_mw_request.state.user.account_id == 2
    token_data_mock.assert_called_once_with('valid-token')


@pytest.mark.asyncio
async def test_dispatch__session_token__return_ok(
    auth_middleware,
    auth_mw_request,
    auth_mw_call_next,
    mocker,
):
    # arrange
    auth_mw_request.headers = {}
    auth_mw_request.cookies = {'token': 'session-token'}
    token_data_mock = mocker.patch(
        'src.shared_kernel.middleware.auth_middleware.PneumaticToken.data',
        new_callable=AsyncMock,
        return_value={'user_id': 3, 'account_id': 4},
    )

    # act
    response = await auth_middleware.dispatch(
        auth_mw_request,
        auth_mw_call_next,
    )

    # assert
    assert response.status_code == 200
    assert auth_mw_request.state.user.user_id == 3
    assert auth_mw_request.state.user.account_id == 4
    token_data_mock.assert_called_once_with('session-token')


@pytest.mark.asyncio
async def test_dispatch__no_auth_required__anonymous(
    auth_middleware_no_auth,
    auth_mw_request,
    auth_mw_call_next,
):
    # arrange
    auth_mw_request.headers = {}
    auth_mw_request.cookies = {}

    # act
    response = await auth_middleware_no_auth.dispatch(
        auth_mw_request,
        auth_mw_call_next,
    )

    # assert
    assert response.status_code == 200
    assert auth_mw_request.state.user.is_anonymous is True


@pytest.mark.asyncio
async def test_dispatch__auth_required_no_token__401(
    auth_middleware,
    auth_mw_request,
    auth_mw_call_next,
):
    # arrange
    auth_mw_request.headers = {}
    auth_mw_request.cookies = {}

    # act
    response = await auth_middleware.dispatch(
        auth_mw_request,
        auth_mw_call_next,
    )

    # assert
    assert response.status_code == 401
    response_data = json.loads(response.body.decode())
    assert response_data['code'] == 'AUTH_001'
    assert 'error_type' not in response_data
    assert 'timestamp' not in response_data
    assert 'request_id' not in response_data


@pytest.mark.asyncio
async def test_dispatch__file_service_auth_cookie__return_ok(
    auth_middleware,
    auth_mw_request,
    auth_mw_call_next,
    mocker,
):
    """Cookie 'file_service_auth' set by Django middleware should work."""
    # arrange
    auth_mw_request.headers = {}
    auth_mw_request.cookies = {'file_service_auth': 'django-token'}
    token_data_mock = mocker.patch(
        'src.shared_kernel.middleware.auth_middleware.PneumaticToken.data',
        new_callable=AsyncMock,
        return_value={'user_id': 5, 'account_id': 6},
    )

    # act
    response = await auth_middleware.dispatch(
        auth_mw_request,
        auth_mw_call_next,
    )

    # assert
    assert response.status_code == 200
    assert auth_mw_request.state.user.user_id == 5
    assert auth_mw_request.state.user.account_id == 6
    token_data_mock.assert_called_once_with('django-token')
