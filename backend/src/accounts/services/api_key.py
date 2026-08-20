import secrets
from typing import Optional

from src.accounts.models import APIKey, User
from src.authentication.tokens import PneumaticToken
from src.generics.base.service import BaseModelService


class APIKeyService(BaseModelService):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.raw_key: Optional[str] = None

    @staticmethod
    def generate_key() -> str:
        """Generate a prefixed API key: <prefix><32 random chars>."""
        return f'{APIKey.API_KEY_PREFIX}{secrets.token_urlsafe(24)}'

    def _create_instance(
        self,
        name: Optional[str] = None,
        target_user: Optional[User] = None,
        **kwargs,
    ):
        target_user = target_user or self.user

        if not name:
            count = APIKey.objects.filter(
                user_id=target_user.id,
            ).count()
            name = f'API Key #{count + 1}'

        raw_key = self.generate_key()

        PneumaticToken.create(
            user=target_user,
            for_api_key=True,
            token=raw_key,
        )

        self.instance = APIKey.objects.create(
            user_id=target_user.id,
            account_id=target_user.account_id,
            name=name,
            token=raw_key,
        )

        self.raw_key = raw_key

    def revoke(self):
        self.instance.is_active = False
        self.instance.save(update_fields=['is_active'])
        cache_key = PneumaticToken.encrypt(self.instance.token)
        PneumaticToken.cache.delete(cache_key)
