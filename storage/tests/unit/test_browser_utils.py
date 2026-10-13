"""Tests for browser navigation detection utilities."""

from unittest.mock import MagicMock

from starlette.requests import Request

from src.shared_kernel.browser_utils import (
    is_browser_navigation,
    redirect_to_error_page,
    redirect_to_login,
)


def test_is_browser_navigation__get_html__true():
    """GET + Accept: text/html → browser navigation."""
    # arrange
    request = MagicMock(spec=Request)
    request.method = 'GET'
    request.headers = {'accept': 'text/html'}

    # act
    result = is_browser_navigation(request)

    # assert
    assert result is True


def test_is_browser_navigation__get_json__false():
    """GET + Accept: application/json → API call."""
    # arrange
    request = MagicMock(spec=Request)
    request.method = 'GET'
    request.headers = {'accept': 'application/json'}

    # act
    result = is_browser_navigation(request)

    # assert
    assert result is False


def test_is_browser_navigation__post_html__false():
    """POST + Accept: text/html → not browser navigation."""
    # arrange
    request = MagicMock(spec=Request)
    request.method = 'POST'
    request.headers = {'accept': 'text/html'}

    # act
    result = is_browser_navigation(request)

    # assert
    assert result is False


def test_is_browser_navigation__mixed_accept_with_html__true():
    """Accept: text/html, application/json → browser navigation."""
    # arrange
    request = MagicMock(spec=Request)
    request.method = 'GET'
    request.headers = {
        'accept': 'text/html, application/xhtml+xml, application/json',
    }

    # act
    result = is_browser_navigation(request)

    # assert
    assert result is True


def test_is_browser_navigation__no_accept__false():
    """No Accept header → not browser navigation."""
    # arrange
    request = MagicMock(spec=Request)
    request.method = 'GET'
    request.headers = {}

    # act
    result = is_browser_navigation(request)

    # assert
    assert result is False


def test_is_browser_navigation__put_html__false():
    """PUT + Accept: text/html → not browser navigation."""
    # arrange
    request = MagicMock(spec=Request)
    request.method = 'PUT'
    request.headers = {'accept': 'text/html'}

    # act
    result = is_browser_navigation(request)

    # assert
    assert result is False


def test_is_browser_navigation__delete_html__false():
    """DELETE + Accept: text/html → not browser navigation."""
    # arrange
    request = MagicMock(spec=Request)
    request.method = 'DELETE'
    request.headers = {'accept': 'text/html'}

    # act
    result = is_browser_navigation(request)

    # assert
    assert result is False


# --- redirect_to_login ---


def test_redirect_to_login__reconstructs_files_url(mocker):
    """Redirect URL should reconstruct user-facing /files/ path."""
    # arrange
    get_settings_mock = mocker.patch(
        'src.shared_kernel.browser_utils.get_settings',
    )
    get_settings_mock.return_value.FRONTEND_URL = 'https://app.pneumatic.app'
    request = MagicMock(spec=Request)
    request.url.path = '/abc-123'
    request.url.query = ''

    # act
    response = redirect_to_login(request)

    # assert
    assert response.status_code == 302
    location = response.headers['location']
    assert location.startswith('https://app.pneumatic.app/auth/signin/')
    assert 'redirectUrl=' in location
    # Should contain /files/ prefix in the encoded URL
    assert '%2Ffiles%2Fabc-123' in location
    get_settings_mock.assert_called_once()


def test_redirect_to_login__preserves_query_params(mocker):
    """Redirect URL should preserve original query parameters."""
    # arrange
    get_settings_mock = mocker.patch(
        'src.shared_kernel.browser_utils.get_settings',
    )
    get_settings_mock.return_value.FRONTEND_URL = 'https://app.pneumatic.app'
    request = MagicMock(spec=Request)
    request.url.path = '/abc-123'
    request.url.query = 'name=test&id=1'

    # act
    response = redirect_to_login(request)

    # assert
    assert response.status_code == 302
    location = response.headers['location']
    assert '%2Ffiles%2Fabc-123' in location
    assert 'name' in location
    assert 'id' in location
    get_settings_mock.assert_called_once()


# --- redirect_to_error_page ---


def test_redirect_to_error_page__url_format(mocker):
    """Should redirect to /error/ on the frontend."""
    # arrange
    get_settings_mock = mocker.patch(
        'src.shared_kernel.browser_utils.get_settings',
    )
    get_settings_mock.return_value.FRONTEND_URL = 'https://app.pneumatic.app'

    # act
    response = redirect_to_error_page()

    # assert
    assert response.status_code == 302
    assert response.headers['location'] == ('https://app.pneumatic.app/error/')
    get_settings_mock.assert_called_once()


def test_redirect_to_error_page__no_trailing_slash(mocker):
    """FRONTEND_URL without trailing slash → valid URL."""
    # arrange
    get_settings_mock = mocker.patch(
        'src.shared_kernel.browser_utils.get_settings',
    )
    get_settings_mock.return_value.FRONTEND_URL = 'https://app.pneumatic.app'

    # act
    response = redirect_to_error_page()

    # assert
    assert '/error/' in response.headers['location']
    get_settings_mock.assert_called_once()
