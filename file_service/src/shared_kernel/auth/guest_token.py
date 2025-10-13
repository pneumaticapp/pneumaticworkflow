from typing import Any, Optional

import jwt
from pydantic import BaseModel

from src.shared_kernel.config import get_settings


class GuestToken(BaseModel):
    """Guest JWT token implementation"""

    token: Optional[str] = None
    payload: dict[str, Any] = {}

    def __init__(self, **data: Any):
        super().__init__(**data)
        if self.token:
            self._decode_token()

    def __str__(self) -> str:
        return self.token or ''

    def __getitem__(self, key: str) -> Any:
        return self.payload[key]

    def __setitem__(self, key: str, value: Any) -> None:
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
        except jwt.InvalidTokenError:
            raise ValueError('Invalid token')
