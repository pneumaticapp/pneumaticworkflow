"""Authentication services"""

from typing import ClassVar

from src.shared_kernel.auth.public_token import EmbedToken, PublicToken
from src.shared_kernel.auth.redis_client import get_redis_client


class PublicAuthService:
    """Public authentication service"""

    HEADER_PREFIX = 'Token'
    HEADER_PARTS = 2
    TOKEN_TYPES: ClassVar[list[type[PublicToken | EmbedToken]]] = [
        PublicToken,
        EmbedToken,
    ]

    @classmethod
    def get_token(
        cls,
        header: str,
    ) -> PublicToken | EmbedToken | None:
        """Get token from header"""
        if not header or not isinstance(header, str):
            return None

        parts = header.split()
        if len(parts) != cls.HEADER_PARTS or parts[0] != cls.HEADER_PREFIX:
            return None

        raw_token = parts[1]

        # Try different token types based on length
        for token_type in cls.TOKEN_TYPES:
            try:
                if len(raw_token) == token_type.token_length:
                    return token_type(raw_token)
            except ValueError:
                continue
        return None

    @classmethod
    async def authenticate_public_token(
        cls,
        token: PublicToken | EmbedToken,
    ) -> dict | None:
        """Authenticate public token"""
        if not token:
            return None

        # Get data from Redis
        redis_client = get_redis_client()
        token_str = str(token)
        return await redis_client.get(f'{token_str}')
