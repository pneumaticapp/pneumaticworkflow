"""HTTP client for external service requests."""

from http import HTTPStatus
from typing import TYPE_CHECKING, Union

import httpx

from src.shared_kernel.auth.user_types import UserType
from src.shared_kernel.exceptions import (
    MSG_EXT_014,
    HttpClientError,
    HttpTimeoutError,
)

if TYPE_CHECKING:
    from src.shared_kernel.auth.dependencies import AuthenticatedUser
    from src.shared_kernel.middleware.auth_middleware import AuthUser


class HttpClient:
    """HTTP client for Django backend requests."""

    def __init__(self, base_url: str) -> None:
        """Initialize HTTP client.

        Args:
            base_url: Base URL for HTTP requests.

        """
        self.base_url = base_url
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Lazy client initialization."""
        if self._client is None:
            self._client = httpx.AsyncClient()
        return self._client

    async def check_file_permission(
        self,
        user: Union['AuthUser', 'AuthenticatedUser'],
        file_id: str,
    ) -> bool:
        """Check file permission based on user type and token."""
        # Form headers based on user type
        headers: dict[str, str] = {}

        if user.auth_type == UserType.AUTHENTICATED and user.token:
            headers['Authorization'] = f'Bearer {user.token}'
        elif user.auth_type == UserType.GUEST_TOKEN and user.token:
            headers['X-Guest-Authorization'] = user.token
        elif user.auth_type == UserType.PUBLIC_TOKEN and user.token:
            headers['X-Public-Authorization'] = f'Token {user.token}'

        try:
            response = await self.client.post(
                url=self.base_url,
                data={'file_id': file_id},
                headers=headers,
            )
        except httpx.TimeoutException as e:
            raise HttpTimeoutError(
                url=self.base_url,
                timeout=30.0,  # Default timeout
                details=str(e),
            ) from e
        except httpx.RequestError as e:
            raise HttpClientError(
                url=self.base_url,
                details=MSG_EXT_014.format(details=str(e)),
            ) from e
        else:
            # 204 - access granted, 403 - access denied
            return response.status_code == HTTPStatus.NO_CONTENT

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
