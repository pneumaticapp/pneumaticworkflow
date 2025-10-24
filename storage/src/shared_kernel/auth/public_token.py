"""Public token implementation"""

import secrets
from abc import ABC, abstractmethod
from typing import Optional


class PublicBaseToken(ABC):
    """Base class for public tokens"""

    @property
    @abstractmethod
    def token_length(self) -> int:
        """Token length"""
        pass

    def __init__(self, token: Optional[str] = None):
        if token:
            self._validate_length(token)
            self.token = token
        else:
            self.token = self._generate_token()

    def __str__(self) -> str:
        """Return token string"""
        return self.token

    def _validate_length(self, token: str) -> None:
        """Validate token length"""
        if len(token) != self.token_length:
            raise ValueError(f'Incorrect token length: {len(token)}')

    def _generate_token(self) -> str:
        """Generate random token"""
        return secrets.token_urlsafe(self.token_length)[: self.token_length]


class PublicToken(PublicBaseToken):
    """Public token implementation"""

    token_length = 8


class EmbedToken(PublicBaseToken):
    """Embed token implementation"""

    token_length = 32
