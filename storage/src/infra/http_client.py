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


class SharedClientHolder:
    """Holder for the shared HTTP client."""

    _instance: httpx.AsyncClient | None = None
    # Explicit timeouts (seconds)
    _TIMEOUT = httpx.Timeout(
        timeout=30.0,  # total request timeout
        connect=10.0,  # connection timeout
    )

    @classmethod
    def get(cls) -> httpx.AsyncClient:
        """Get or create shared HTTP client instance."""
        if cls._instance is None:
            cls._instance = httpx.AsyncClient(
                timeout=cls._TIMEOUT,
            )
        return cls._instance

    @classmethod
    async def close(cls) -> None:
        """Close shared HTTP client."""
        if cls._instance is not None:
            await cls._instance.aclose()
            cls._instance = None


def get_shared_client() -> httpx.AsyncClient:
    """Get or create shared HTTP client."""
    return SharedClientHolder.get()


async def close_shared_client() -> None:
    """Close shared HTTP client."""
    await SharedClientHolder.close()


class HttpClient:
    """HTTP client for Django backend requests."""

    def __init__(self, base_url: str) -> None:
        """Initialize HTTP client.

        Args:
            base_url: Base URL for HTTP requests.

        """
        self.base_url = base_url

    @property
    def client(self) -> httpx.AsyncClient:
        """Shared client instance."""
        return get_shared_client()

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
                timeout=SharedClientHolder._TIMEOUT.read or 30.0,
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
        # No-op since we use a shared global client managed by lifespan
