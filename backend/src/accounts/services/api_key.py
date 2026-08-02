from typing import Optional

from src.accounts.models import APIKey
from src.authentication.tokens import PneumaticToken
from src.generics.base.service import BaseModelService


class APIKeyService(BaseModelService):

    def _create_instance(
        self,
        name: Optional[str] = None,
        **kwargs,
    ):
        """Create a new API key. Sets self.instance and returns raw_key."""

        if name is None:
            count = APIKey.objects.filter(
                user=self.user,
                is_active=True,
            ).count()
            name = f'API Key #{count + 1}'

        raw_key = APIKey.generate_key()
        cache_token = PneumaticToken.encrypt(raw_key)

        PneumaticToken.create(
            user=self.user,
            for_api_key=True,
            token=raw_key,
        )

        self.instance = APIKey.objects.create(
            user=self.user,
            account=self.account,
            name=name,
            prefix=raw_key[:16],
            key_hash=APIKey.hash_key(raw_key),
            cache_token=cache_token,
        )

        self._raw_key = raw_key

    def create(self, **kwargs):
        super().create(**kwargs)
        return self.instance, self._raw_key

    def revoke(self):
        """Deactivate the key and invalidate its cache entry."""
        self.instance.is_active = False
        self.instance.save(update_fields=['is_active'])
        if self.instance.cache_token:
            PneumaticToken.cache.delete(self.instance.cache_token)
