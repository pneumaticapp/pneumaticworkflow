from types import SimpleNamespace

from rest_framework.exceptions import AuthenticationFailed

from src.authentication.services.user_auth import (
    CookieTokenAuthentication,
)


def test_authenticate__bearer_ok__returns_result(mocker):
    # arrange
    auth = CookieTokenAuthentication()
    request = SimpleNamespace(
        method='GET',
        META={},
        COOKIES={'token': 'cookie-tok'},
        session={},
        token_type=None,
        is_superuser=False,
    )
    expected = (mocker.Mock(), mocker.Mock())
    parent_auth_mock = mocker.patch(
        'src.authentication.services.user_auth'
        '.PneumaticTokenAuthentication.authenticate',
        return_value=expected,
    )
    creds_mock = mocker.patch.object(
        auth,
        'authenticate_credentials',
    )

    # act
    result = auth.authenticate(request)

    # assert
    parent_auth_mock.assert_called_once_with(request)
    creds_mock.assert_not_called()
    assert result is expected


def test_authenticate__auth_failed_get_cookie__ok(mocker):
    # arrange
    auth = CookieTokenAuthentication()
    request = SimpleNamespace(
        method='GET',
        META={},
        COOKIES={'token': 'test-token-123'},
        session={},
        token_type=None,
        is_superuser=False,
    )
    expected = (mocker.Mock(), mocker.Mock())
    parent_auth_mock = mocker.patch(
        'src.authentication.services.user_auth'
        '.PneumaticTokenAuthentication.authenticate',
        side_effect=AuthenticationFailed(),
    )
    creds_mock = mocker.patch.object(
        auth,
        'authenticate_credentials',
        return_value=expected,
    )
    apply_ctx_mock = mocker.patch.object(
        auth,
        '_apply_auth_context',
    )

    # act
    result = auth.authenticate(request)

    # assert
    parent_auth_mock.assert_called_once_with(request)
    creds_mock.assert_called_once_with('test-token-123')
    apply_ctx_mock.assert_called_once_with(
        request,
        expected,
    )
    assert result is expected


def test_authenticate__bearer_none_get_cookie__ok(mocker):
    # arrange
    auth = CookieTokenAuthentication()
    request = SimpleNamespace(
        method='GET',
        META={},
        COOKIES={'token': 'cookie-tok'},
        session={},
        token_type=None,
        is_superuser=False,
    )
    expected = (mocker.Mock(), mocker.Mock())
    parent_auth_mock = mocker.patch(
        'src.authentication.services.user_auth'
        '.PneumaticTokenAuthentication.authenticate',
        return_value=None,
    )
    creds_mock = mocker.patch.object(
        auth,
        'authenticate_credentials',
        return_value=expected,
    )
    apply_ctx_mock = mocker.patch.object(
        auth,
        '_apply_auth_context',
    )

    # act
    result = auth.authenticate(request)

    # assert
    parent_auth_mock.assert_called_once_with(request)
    creds_mock.assert_called_once_with('cookie-tok')
    apply_ctx_mock.assert_called_once_with(
        request,
        expected,
    )
    assert result is expected


def test_authenticate__head_cookie__ok(mocker):
    # arrange
    auth = CookieTokenAuthentication()
    request = SimpleNamespace(
        method='HEAD',
        META={},
        COOKIES={'token': 'head-token'},
        session={},
        token_type=None,
        is_superuser=False,
    )
    expected = (mocker.Mock(), mocker.Mock())
    parent_auth_mock = mocker.patch(
        'src.authentication.services.user_auth'
        '.PneumaticTokenAuthentication.authenticate',
        side_effect=AuthenticationFailed(),
    )
    creds_mock = mocker.patch.object(
        auth,
        'authenticate_credentials',
        return_value=expected,
    )
    apply_ctx_mock = mocker.patch.object(
        auth,
        '_apply_auth_context',
    )

    # act
    result = auth.authenticate(request)

    # assert
    parent_auth_mock.assert_called_once_with(request)
    creds_mock.assert_called_once_with('head-token')
    apply_ctx_mock.assert_called_once_with(
        request,
        expected,
    )
    assert result is expected


def test_authenticate__options_cookie__ok(mocker):
    # arrange
    auth = CookieTokenAuthentication()
    request = SimpleNamespace(
        method='OPTIONS',
        META={},
        COOKIES={'token': 'options-token'},
        session={},
        token_type=None,
        is_superuser=False,
    )
    expected = (mocker.Mock(), mocker.Mock())
    parent_auth_mock = mocker.patch(
        'src.authentication.services.user_auth'
        '.PneumaticTokenAuthentication.authenticate',
        side_effect=AuthenticationFailed(),
    )
    creds_mock = mocker.patch.object(
        auth,
        'authenticate_credentials',
        return_value=expected,
    )
    apply_ctx_mock = mocker.patch.object(
        auth,
        '_apply_auth_context',
    )

    # act
    result = auth.authenticate(request)

    # assert
    parent_auth_mock.assert_called_once_with(request)
    creds_mock.assert_called_once_with('options-token')
    apply_ctx_mock.assert_called_once_with(
        request,
        expected,
    )
    assert result is expected


def test_authenticate__post_cookie__blocked(mocker):
    # arrange
    auth = CookieTokenAuthentication()
    request = SimpleNamespace(
        method='POST',
        META={},
        COOKIES={'token': 'test-token-123'},
        session={},
        token_type=None,
        is_superuser=False,
    )
    parent_auth_mock = mocker.patch(
        'src.authentication.services.user_auth'
        '.PneumaticTokenAuthentication.authenticate',
        side_effect=AuthenticationFailed(),
    )
    creds_mock = mocker.patch.object(
        auth,
        'authenticate_credentials',
    )

    # act
    result = auth.authenticate(request)

    # assert
    parent_auth_mock.assert_called_once_with(request)
    creds_mock.assert_not_called()
    assert result is None
    assert request.session['is_authenticated'] is False
    assert request.token_type is None
    assert request.is_superuser is False


def test_authenticate__put_cookie__blocked(mocker):
    # arrange
    auth = CookieTokenAuthentication()
    request = SimpleNamespace(
        method='PUT',
        META={},
        COOKIES={'token': 'test-token-123'},
        session={},
        token_type=None,
        is_superuser=False,
    )
    parent_auth_mock = mocker.patch(
        'src.authentication.services.user_auth'
        '.PneumaticTokenAuthentication.authenticate',
        side_effect=AuthenticationFailed(),
    )
    creds_mock = mocker.patch.object(
        auth,
        'authenticate_credentials',
    )

    # act
    result = auth.authenticate(request)

    # assert
    parent_auth_mock.assert_called_once_with(request)
    creds_mock.assert_not_called()
    assert result is None
    assert request.session['is_authenticated'] is False
    assert request.token_type is None
    assert request.is_superuser is False


def test_authenticate__delete_cookie__blocked(mocker):
    # arrange
    auth = CookieTokenAuthentication()
    request = SimpleNamespace(
        method='DELETE',
        META={},
        COOKIES={'token': 'test-token-123'},
        session={},
        token_type=None,
        is_superuser=False,
    )
    parent_auth_mock = mocker.patch(
        'src.authentication.services.user_auth'
        '.PneumaticTokenAuthentication.authenticate',
        side_effect=AuthenticationFailed(),
    )
    creds_mock = mocker.patch.object(
        auth,
        'authenticate_credentials',
    )

    # act
    result = auth.authenticate(request)

    # assert
    parent_auth_mock.assert_called_once_with(request)
    creds_mock.assert_not_called()
    assert result is None
    assert request.session['is_authenticated'] is False
    assert request.token_type is None
    assert request.is_superuser is False


def test_authenticate__no_cookie__returns_none(mocker):
    # arrange
    auth = CookieTokenAuthentication()
    request = SimpleNamespace(
        method='GET',
        META={},
        COOKIES={},
        session={},
        token_type=None,
        is_superuser=False,
    )
    parent_auth_mock = mocker.patch(
        'src.authentication.services.user_auth'
        '.PneumaticTokenAuthentication.authenticate',
        side_effect=AuthenticationFailed(),
    )
    creds_mock = mocker.patch.object(
        auth,
        'authenticate_credentials',
    )

    # act
    result = auth.authenticate(request)

    # assert
    parent_auth_mock.assert_called_once_with(request)
    creds_mock.assert_not_called()
    assert result is None
    assert request.session['is_authenticated'] is False
    assert request.token_type is None
    assert request.is_superuser is False


def test_authenticate__invalid_cookie__returns_none(mocker):
    # arrange
    auth = CookieTokenAuthentication()
    request = SimpleNamespace(
        method='GET',
        META={},
        COOKIES={'token': 'bad-token'},
        session={},
        token_type=None,
        is_superuser=False,
    )
    parent_auth_mock = mocker.patch(
        'src.authentication.services.user_auth'
        '.PneumaticTokenAuthentication.authenticate',
        side_effect=AuthenticationFailed(),
    )
    creds_mock = mocker.patch.object(
        auth,
        'authenticate_credentials',
        return_value=None,
    )

    # act
    result = auth.authenticate(request)

    # assert
    parent_auth_mock.assert_called_once_with(request)
    creds_mock.assert_called_once_with('bad-token')
    assert result is None
    assert request.session['is_authenticated'] is False
    assert request.token_type is None
    assert request.is_superuser is False


def test_authenticate__empty_cookie__returns_none(mocker):
    # arrange
    auth = CookieTokenAuthentication()
    request = SimpleNamespace(
        method='GET',
        META={},
        COOKIES={'token': ''},
        session={},
        token_type=None,
        is_superuser=False,
    )
    parent_auth_mock = mocker.patch(
        'src.authentication.services.user_auth'
        '.PneumaticTokenAuthentication.authenticate',
        side_effect=AuthenticationFailed(),
    )
    creds_mock = mocker.patch.object(
        auth,
        'authenticate_credentials',
    )

    # act
    result = auth.authenticate(request)

    # assert
    parent_auth_mock.assert_called_once_with(request)
    creds_mock.assert_not_called()
    assert result is None
    assert request.session['is_authenticated'] is False
    assert request.token_type is None
    assert request.is_superuser is False
