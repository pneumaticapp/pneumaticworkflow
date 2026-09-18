"""Tests for authentication middleware."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.shared_kernel.auth.public_token import EmbedToken, PublicToken
from src.shared_kernel.auth.user_types import (
    JournalAuthType,
    JournalUserType,
    UserType,
)
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


@pytest.mark.asyncio
async def test_dispatch__browser_get_anonymous__redirect_to_login(
    auth_middleware,
    auth_mw_request,
    auth_mw_call_next,
    mocker,
):
    """Browser GET (Accept: text/html) without auth → 302 to login."""
    # arrange
    auth_mw_request.method = 'GET'
    auth_mw_request.headers = {'accept': 'text/html'}
    auth_mw_request.cookies = {}
    auth_mw_request.url = MagicMock(path='/abc-123', query='')
    get_settings_mock = mocker.patch(
        'src.shared_kernel.browser_utils.get_settings',
    )
    get_settings_mock.return_value.FRONTEND_URL = 'https://app.example.com'

    # act
    response = await auth_middleware.dispatch(
        auth_mw_request,
        auth_mw_call_next,
    )

    # assert
    assert response.status_code == 302
    location = response.headers['location']
    assert 'auth/signin' in location
    assert 'redirectUrl=' in location
    get_settings_mock.assert_called_once()


@pytest.mark.asyncio
async def test_dispatch__api_get_anonymous__returns_401_json(
    auth_middleware,
    auth_mw_request,
    auth_mw_call_next,
):
    """API GET (Accept: application/json) without auth → 401 JSON."""
    # arrange
    auth_mw_request.method = 'GET'
    auth_mw_request.headers = {'accept': 'application/json'}
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


@pytest.mark.asyncio
async def test_dispatch__browser_post_anonymous__returns_401_json(
    auth_middleware,
    auth_mw_request,
    auth_mw_call_next,
):
    """POST with Accept: text/html → 401 JSON, not redirect."""
    # arrange
    auth_mw_request.method = 'POST'
    auth_mw_request.headers = {'accept': 'text/html'}
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


@pytest.mark.asyncio
async def test_dispatch__authenticated_browser_get__passes_through(
    auth_middleware,
    auth_mw_request,
    auth_mw_call_next,
    mocker,
):
    """Browser GET with valid token → normal response, no redirect."""
    # arrange
    auth_mw_request.method = 'GET'
    auth_mw_request.headers = {
        'accept': 'text/html',
        'Authorization': 'Bearer valid-token',
    }
    auth_mw_request.cookies = {}
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
    token_data_mock.assert_called_once_with('valid-token')


@pytest.mark.asyncio
async def test_authenticate_token__api_key_token__is_api_key(
    auth_middleware,
    mocker,
):
    # arrange
    token = 'api-key-token'
    token_data_mock = mocker.patch(
        'src.shared_kernel.middleware.auth_middleware.PneumaticToken.data',
        new_callable=AsyncMock,
        return_value={'user_id': 1, 'account_id': 2, 'for_api_key': True},
    )

    # act
    result = await auth_middleware.authenticate_token(token)

    # assert
    assert result is not None
    assert result.is_api_key is True
    assert result.journal_auth_type == JournalAuthType.API
    token_data_mock.assert_called_once_with(token)


@pytest.mark.asyncio
async def test_authenticate_token__session_token__not_api_key(
    auth_middleware,
    mocker,
):
    # arrange
    token = 'session-token'
    token_data_mock = mocker.patch(
        'src.shared_kernel.middleware.auth_middleware.PneumaticToken.data',
        new_callable=AsyncMock,
        return_value={'user_id': 1, 'account_id': 2},
    )

    # act
    result = await auth_middleware.authenticate_token(token)

    # assert
    assert result is not None
    assert result.is_api_key is False
    assert result.journal_auth_type == JournalAuthType.USER
    token_data_mock.assert_called_once_with(token)


@pytest.mark.asyncio
async def test_authenticate_public_token__shared_token__not_embed(
    auth_middleware,
    mocker,
):
    # arrange
    token = PublicToken(token='a' * PublicToken.token_length)
    get_token_mock = mocker.patch(
        'src.shared_kernel.middleware.auth_middleware.'
        'PublicAuthService.get_token',
        return_value=token,
    )
    authenticate_mock = mocker.patch(
        'src.shared_kernel.middleware.auth_middleware.'
        'PublicAuthService.authenticate_public_token',
        new_callable=AsyncMock,
        return_value={'account_id': 2},
    )

    # act
    result = await auth_middleware.authenticate_public_token('Token a')

    # assert
    assert result is not None
    assert result.auth_type == UserType.PUBLIC_TOKEN
    assert result.user_id is None
    assert result.account_id == 2
    assert result.token == str(token)
    assert result.is_embed_token is False
    assert result.journal_auth_type == JournalAuthType.SHARED
    get_token_mock.assert_called_once_with('Token a')
    authenticate_mock.assert_awaited_once_with(token)


@pytest.mark.asyncio
async def test_authenticate_public_token__embed_token__is_embed(
    auth_middleware,
    mocker,
):
    # arrange
    token = EmbedToken(token='b' * EmbedToken.token_length)
    get_token_mock = mocker.patch(
        'src.shared_kernel.middleware.auth_middleware.'
        'PublicAuthService.get_token',
        return_value=token,
    )
    authenticate_mock = mocker.patch(
        'src.shared_kernel.middleware.auth_middleware.'
        'PublicAuthService.authenticate_public_token',
        new_callable=AsyncMock,
        return_value={'account_id': 2},
    )

    # act
    result = await auth_middleware.authenticate_public_token('Token b')

    # assert
    assert result is not None
    assert result.auth_type == UserType.PUBLIC_TOKEN
    assert result.is_embed_token is True
    assert result.journal_auth_type == JournalAuthType.EMBEDDED
    get_token_mock.assert_called_once_with('Token b')
    authenticate_mock.assert_awaited_once_with(token)


def test_auth_user__authenticated__journal_user_with_user_auth():
    # arrange
    user = AuthUser(auth_type=UserType.AUTHENTICATED, user_id=1, account_id=2)

    # act
    user_type = user.journal_user_type
    auth_type = user.journal_auth_type

    # assert
    assert user_type == JournalUserType.USER
    assert auth_type == JournalAuthType.USER


def test_auth_user__api_key__journal_user_with_api_auth():
    # arrange
    user = AuthUser(
        auth_type=UserType.AUTHENTICATED,
        user_id=1,
        account_id=2,
        is_api_key=True,
    )

    # act
    user_type = user.journal_user_type
    auth_type = user.journal_auth_type

    # assert
    assert user_type == JournalUserType.USER
    assert auth_type == JournalAuthType.API


def test_auth_user__guest_token__journal_guest_with_guest_auth():
    # arrange
    user = AuthUser(auth_type=UserType.GUEST_TOKEN, user_id=1, account_id=2)

    # act
    user_type = user.journal_user_type
    auth_type = user.journal_auth_type

    # assert
    assert user_type == JournalUserType.GUEST
    assert auth_type == JournalAuthType.GUEST


def test_auth_user__public_token__no_journal_user_with_shared_auth():
    # arrange
    user = AuthUser(auth_type=UserType.PUBLIC_TOKEN, account_id=2)

    # act
    user_type = user.journal_user_type
    auth_type = user.journal_auth_type

    # assert
    assert user_type is None
    assert auth_type == JournalAuthType.SHARED


def test_auth_user__embed_token__no_journal_user_with_embedded_auth():
    # arrange
    user = AuthUser(
        auth_type=UserType.PUBLIC_TOKEN,
        account_id=2,
        is_embed_token=True,
    )

    # act
    user_type = user.journal_user_type
    auth_type = user.journal_auth_type

    # assert
    assert user_type is None
    assert auth_type == JournalAuthType.EMBEDDED


def test_auth_user__anonymous__no_journal_user_no_auth():
    # arrange
    user = AuthUser(auth_type=UserType.ANONYMOUS)

    # act
    user_type = user.journal_user_type
    auth_type = user.journal_auth_type

    # assert
    assert user_type is None
    assert auth_type is None
