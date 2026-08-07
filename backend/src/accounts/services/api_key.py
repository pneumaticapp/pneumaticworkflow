from typing import Optional, Tuple

from src.accounts.models import APIKey, User
from src.authentication.tokens import PneumaticToken
from src.generics.base.service import BaseModelService


class APIKeyService(BaseModelService):

    _raw_key: str = ''

    def _create_key_for(
        self,
        target_user: 'User',
        name: Optional[str] = None,
    ):

        if not name:
            count = APIKey.objects.filter(
                user=target_user,
                is_active=True,
            ).count()
            name = f'API Key #{count + 1}'

        raw_key = APIKey.generate_key()
        cache_token = PneumaticToken.encrypt(raw_key)

        PneumaticToken.create(
            user=target_user,
            for_api_key=True,
            token=raw_key,
        )

        self.instance = APIKey.objects.create(
            user=target_user,
            account=target_user.account,
            name=name,
            prefix=raw_key[:16],
            key_hash=APIKey.hash_key(raw_key),
            cache_token=cache_token,
        )

        self._raw_key = raw_key

    def _create_instance(
        self,
        name: Optional[str] = None,
        **kwargs,
    ):
        self._create_key_for(target_user=self.user, name=name)

    def create(self, **kwargs) -> Tuple[APIKey, str]:
        super().create(**kwargs)
        return self.instance, self._raw_key

    def create_for_user(
        self,
        target_user: 'User',
        name: Optional[str] = None,
    ) -> Tuple[APIKey, str]:
        self._create_key_for(target_user=target_user, name=name)
        return self.instance, self._raw_key

    def revoke(self):
        self.instance.is_active = False
        self.instance.save(update_fields=['is_active'])
        if self.instance.cache_token:
            PneumaticToken.cache.delete(self.instance.cache_token)
