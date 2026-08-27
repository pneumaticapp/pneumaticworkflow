from typing import List, Tuple
from urllib.parse import urlparse

from src.ai.enums import AIVendor
from src.ai.models import AIProvider
from src.ai.serializers import AIModelSerializer
from src.ai.services.vendors.anthropic import AnthropicVendor
from src.ai.services.vendors.azure import AzureOpenAIVendor
from src.ai.services.vendors.gemini import GeminiVendor
from src.ai.services.vendors.openai_compatible import (
    OpenAICompatibleVendor,
)
from src.generics.base.service import BaseModelService
from src.generics.mixins.services import CacheMixin, EncryptionMixin


class AIProviderService(
    BaseModelService,
    CacheMixin,
    EncryptionMixin,
):
    cache_key_prefix = '_models'
    cache_timeout = 86400  # 1 day
    serializer_cls = AIModelSerializer

    @property
    def _get_vendor_cls(self):
        vendor_classes = {
            AIVendor.ANTHROPIC: AnthropicVendor,
            AIVendor.GEMINI: GeminiVendor,
            AIVendor.AZURE_OPENAI: AzureOpenAIVendor,
        }
        return vendor_classes.get(
            self.instance.vendor,
            OpenAICompatibleVendor,
        )

    def _identify_vendor(
        self,
        base_url: str,
    ) -> Tuple[str, str]:

        hostname = (urlparse(base_url).hostname or '').lower()
        vendor = AIVendor.CODE_BY_HOST.get(hostname)
        if vendor is None:
            vendor = AIVendor.OPENAI_COMPATIBLE
        name = AIVendor.NAME_BY_CODE[vendor]
        return name, vendor

    def _create_instance(
        self,
        base_url: str,
        api_key: str,
        is_active: bool = True,
        **kwargs,
    ):
        name, vendor = self._identify_vendor(base_url)
        self.instance = AIProvider.objects.create(
            account=self.account,
            name=name,
            vendor=vendor,
            base_url=base_url,
            is_active=is_active,
            api_key_encrypted=self.encrypt(api_key),
        )
        return self.instance

    def partial_update(
        self,
        force_save=True,
        **update_kwargs,
    ) -> AIProvider:

        if 'api_key' in update_kwargs:
            update_kwargs['api_key_encrypted'] = self.encrypt(
                update_kwargs.pop('api_key'),
            )
        if 'base_url' in update_kwargs:
            name, vendor = self._identify_vendor(update_kwargs['base_url'])
            update_kwargs['vendor'] = vendor
            update_kwargs['name'] = name
        return super().partial_update(
            force_save=force_save,
            **update_kwargs,
        )

    def delete(self) -> None:
        self._delete_cache(key=self.instance.name)
        super().delete()

    def get_models(self) -> List[dict]:
        cache_key = f'{self.user.id}_{self.instance.name}'
        models = self._get_cache(key=cache_key, default=[])
        if not models:
            vendor = self._get_vendor_cls(
                instance=self.instance,
                user=self.user,
            )
            models = vendor.get_models()
            self._set_cache(key=cache_key, value=models)
        return models
