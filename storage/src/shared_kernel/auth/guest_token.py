from typing import Any

import jwt
from pydantic import BaseModel

from src.shared_kernel.config import get_settings


class GuestToken(BaseModel):
    """Guest JWT token implementation"""

    token: str | None = None
    payload: dict[str, Any] = {}

    def __init__(self, **data: str | int | None) -> None:
        super().__init__(**data)
        if self.token:
            self._decode_token()

    def __str__(self) -> str:
        return self.token or ''

    def __getitem__(self, key: str) -> str | int | None:
        return self.payload[key]

    def __setitem__(self, key: str, value: str | int | None) -> None:
        self.payload[key] = value

    def _decode_token(self) -> None:
        """Decode JWT token"""
        try:
            if not self.token:
                return
            settings = get_settings()
            self.payload = jwt.decode(
                self.token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
        except jwt.InvalidTokenError as e:
            error_msg = 'Invalid token'
            raise ValueError(error_msg) from e
