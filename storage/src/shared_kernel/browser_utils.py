"""Browser navigation detection utilities.

Detects browser page navigation (direct URL entry, link clicks)
vs API calls (fetch/axios with Accept: application/json).
Used to serve user-friendly redirects instead of raw JSON errors.
"""

from urllib.parse import quote

from starlette.requests import Request
from starlette.responses import RedirectResponse

from src.shared_kernel.config import get_settings


def is_browser_navigation(request: Request) -> bool:
    """Check if request is a browser page navigation.

    Browser navigation = GET + Accept contains text/html.
    API calls typically use Accept: application/json.

    Args:
        request: Incoming HTTP request.

    Returns:
        True if this looks like a browser navigating to a page.

    """
    if request.method != 'GET':
        return False
    accept = request.headers.get('accept', '')
    return 'text/html' in accept


def redirect_to_login(request: Request) -> RedirectResponse:
    """Redirect to frontend login page with return URL.

    After successful login, the frontend will redirect the user
    back to the original file URL.

    Note: nginx strips the /files/ prefix before proxying to this service,
    so we reconstruct the user-facing URL from FRONTEND_URL + /files/ + path.

    Args:
        request: Original request (used to build redirectUrl param).

    Returns:
        302 redirect to /auth/signin/?redirectUrl=...

    """
    settings = get_settings()
    # Reconstruct the user-facing URL (nginx strips /files/ prefix)
    original_path = request.url.path
    query = str(request.url.query)
    file_url = f'{settings.FRONTEND_URL}/files{original_path}'
    if query:
        file_url = f'{file_url}?{query}'
    encoded_url = quote(file_url, safe='')
    login_url = (
        f'{settings.FRONTEND_URL}/auth/signin/?redirectUrl={encoded_url}'
    )
    return RedirectResponse(url=login_url, status_code=302)


def redirect_to_error_page() -> RedirectResponse:
    """Redirect to frontend error page.

    Used for 403/404/5xx errors when the user navigates
    directly to a file URL in the browser.

    Returns:
        302 redirect to /error/

    """
    settings = get_settings()
    error_url = f'{settings.FRONTEND_URL}/error/'
    return RedirectResponse(url=error_url, status_code=302)
