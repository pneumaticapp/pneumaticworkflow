from typing import Optional

from src.accounts.models import APIKey, User
from src.authentication.tokens import PneumaticToken


class APIKeyService:

    @staticmethod
    def create(
        user: User,
        name: Optional[str] = None,
    ) -> tuple:
        """Create a new API key. Returns (api_key, raw_key)."""

        if name is None:
            count = APIKey.objects.filter(
                user=user,
                is_active=True,
            ).count()
            name = f'API Key #{count + 1}'

        raw_key = APIKey.generate_key()
        cache_token = PneumaticToken.encrypt(raw_key)

        PneumaticToken.create(
            user=user,
            for_api_key=True,
            token=raw_key,
        )

        api_key = APIKey.objects.create(
            user=user,
            account=user.account,
            name=name,
            prefix=raw_key[:16],
            key_hash=APIKey.hash_key(raw_key),
            cache_token=cache_token,
        )

        return api_key, raw_key
