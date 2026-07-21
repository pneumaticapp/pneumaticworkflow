from types import SimpleNamespace

from src.authentication.enums import AuthTokenType
from src.authentication.services.user_auth import (
    PneumaticTokenAuthentication,
)


def test_apply_auth_context__none_result__clears_auth(mocker):
    # arrange
    auth = PneumaticTokenAuthentication()
    request = SimpleNamespace(
        session={},
        token_type='stale',
        is_superuser=True,
    )
    token_data_mock = mocker.patch(
        'src.authentication.services.user_auth'
        '.PneumaticToken.data',
    )
    activate_mock = mocker.patch(
        'src.authentication.services.user_auth'
        '.translation.activate',
    )

    # act
    auth._apply_auth_context(request, None)

    # assert
    token_data_mock.assert_not_called()
    activate_mock.assert_not_called()
    assert request.session['is_authenticated'] is False
    assert request.token_type is None
    assert request.is_superuser is False


def test_apply_auth_context__cached_api__sets_api_type(mocker):
    # arrange
    auth = PneumaticTokenAuthentication()
    user = mocker.Mock(language='en')
    token = mocker.Mock(key='api-token')
    request = SimpleNamespace(
        session={},
        token_type=None,
        is_superuser=False,
    )
    token_data_mock = mocker.patch(
        'src.authentication.services.user_auth'
        '.PneumaticToken.data',
        return_value={
            'for_api_key': True,
            'is_superuser': False,
        },
    )
    activate_mock = mocker.patch(
        'src.authentication.services.user_auth'
        '.translation.activate',
    )

    # act
    auth._apply_auth_context(request, (user, token))

    # assert
    token_data_mock.assert_called_once_with('api-token')
    activate_mock.assert_called_once_with('en')
    assert request.session['is_authenticated'] is True
    assert request.token_type == AuthTokenType.API
    assert request.is_superuser is False


def test_apply_auth_context__cached_user_super__ok(mocker):
    # arrange
    auth = PneumaticTokenAuthentication()
    user = mocker.Mock(language='ru')
    token = mocker.Mock(key='user-token')
    request = SimpleNamespace(
        session={},
        token_type=None,
        is_superuser=False,
    )
    token_data_mock = mocker.patch(
        'src.authentication.services.user_auth'
        '.PneumaticToken.data',
        return_value={
            'for_api_key': False,
            'is_superuser': True,
        },
    )
    activate_mock = mocker.patch(
        'src.authentication.services.user_auth'
        '.translation.activate',
    )

    # act
    auth._apply_auth_context(request, (user, token))

    # assert
    token_data_mock.assert_called_once_with('user-token')
    activate_mock.assert_called_once_with('ru')
    assert request.session['is_authenticated'] is True
    assert request.token_type == AuthTokenType.USER
    assert request.is_superuser is True


def test_apply_auth_context__no_cache__defaults_user(mocker):
    # arrange
    auth = PneumaticTokenAuthentication()
    user = mocker.Mock(language='en')
    token = mocker.Mock(key='missing-cache')
    request = SimpleNamespace(
        session={},
        token_type=None,
        is_superuser=True,
    )
    token_data_mock = mocker.patch(
        'src.authentication.services.user_auth'
        '.PneumaticToken.data',
        return_value=None,
    )
    activate_mock = mocker.patch(
        'src.authentication.services.user_auth'
        '.translation.activate',
    )

    # act
    auth._apply_auth_context(request, (user, token))

    # assert
    token_data_mock.assert_called_once_with('missing-cache')
    activate_mock.assert_called_once_with('en')
    assert request.session['is_authenticated'] is True
    assert request.token_type == AuthTokenType.USER
    assert request.is_superuser is False
