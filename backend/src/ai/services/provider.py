from typing import List, Optional
from src.ai.enums import AIVendor
from src.ai.exceptions import AIProviderInUseException
from src.ai.models import AIAgent, AIProvider
from src.ai.serializers import AIModelSerializer
from src.ai.services.handlers import BaseHandler

from src.generics.base.service import BaseModelService
from src.generics.mixins.services import CacheMixin, EncryptionMixin
from src.processes.models.workflows.task import Task
from src.ai.services.config import AI_VENDORS_CONFIG


class AIProviderService(
    BaseModelService,
    CacheMixin,
    EncryptionMixin,
):
    cache_key_prefix = '_models'
    cache_timeout = 86400  # 1 day
    serializer_cls = AIModelSerializer

    def _create_instance(
        self,
        name: str,
        base_url: str,
        api_key: str,
        vendor: Optional[str] = None,
        **kwargs,
    ):
        self.instance = AIProvider.objects.create(
            account=self.account,
            name=name,
            vendor=vendor,
            base_url=base_url,
            api_key_encrypted=self.encrypt(api_key),
        )
        return self.instance

    def create_by_vendor(
        self,
        api_key: str,
        vendor: AIVendor.LITERALS,
    ) -> AIProvider:
        config = AI_VENDORS_CONFIG[vendor]
        return self.create(
            name=config['name'],
            base_url=config['base_url'],
            api_key=api_key,
            vendor=vendor,
        )

    def partial_update(
        self,
        force_save=True,
        **update_kwargs,
    ) -> AIProvider:

        if 'api_key' in update_kwargs:
            update_kwargs['api_key_encrypted'] = self.encrypt(
                update_kwargs.pop('api_key'),
            )
        return super().partial_update(
            force_save=force_save,
            **update_kwargs,
        )

    def delete(self) -> None:
        if self.instance.ai_agents.exists():
            raise AIProviderInUseException
        self._delete_cache(key=self.instance.name)
        super().delete()

    def _get_handler(
        self,
        agent: Optional[AIAgent] = None,
        task: Optional[Task] = None,
    ) -> BaseHandler:

        config = AI_VENDORS_CONFIG[self.instance.type]
        handler_cls = config['handler']
        return handler_cls(
            provider=self.instance,
            account=self.account,
            config=config,
            agent=agent,
            task=task,
        )

    def get_models(self) -> List[dict]:
        cache_key = f'{self.user.id}_{self.instance.name}'
        models = self._get_cache(key=cache_key, default=[])
        if not models:
            handler = self._get_handler()
            models = handler.get_models()
            self._set_cache(key=cache_key, value=models)
        return models

    def get_completion(
        self,
        system_message: str,
        user_message: str,
        model: str,
        agent: AIAgent,
        task: Task,
    ) -> str:
        handler = self._get_handler(agent=agent, task=task)
        return handler.get_completion(
            system_message=system_message,
            user_message=user_message,
            model=model,
        )
