from typing import List, Optional
from src.ai.enums import AIVendor
from src.ai.exceptions import (
    AIHandlerException,
    AIHandlerPermissionDenied,
    AIHandlerUnauthorized,
    AIProviderException,
    AIProviderInUseException,
    AIProviderModelsNotResponded,
)
from src.ai.messages import (
    MSG_AI_0006,
    MSG_AI_0007,
)
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

    """ Manages the AI providers of an account: creates them after
        a check request, stores the API key encrypted, caches the list
        of the provider models and sends the completion requests.
        The vendor handler errors are converted to AIProviderException.

        AIProviderService(user=owner, instance=<AIProvider 3>)
        .get_completion(system_message='...', user_message='...',
                        model='openai/gpt-4o')
        -> 'Hello world' """

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

        """ Creates the provider if its models are available
            and one of them answers a test request.

            Params:
              name: 'OpenAI'
              base_url: 'https://api.openai.com/v1'
              api_key: 'sk-proj-...', stored encrypted
              vendor: 'openai', AIVendor.CUSTOM if not passed

            Result:
              <AIProvider 'OpenAI'>, its models are cached

            Raises:
              AIProviderException: the models list or the test request
                failed
              AIProviderModelsNotResponded: no model answered the test
                request """

        self.instance = AIProvider(
            account=self.account,
            name=name,
            base_url=base_url,
            api_key_encrypted=self.encrypt(api_key),
            vendor=vendor or AIVendor.CUSTOM,
        )
        models = self.get_models()
        self._create_first_completion(models)
        self.instance.save()
        return self.instance

    def create(self, **kwargs) -> AIProvider:

        """ Creates the provider, see _create_instance.

            Params:
              kwargs: {'name': 'OpenAI',
                'base_url': 'https://api.openai.com/v1',
                'api_key': 'sk-proj-...'}

            Result:
              <AIProvider 'OpenAI'> """

        self._create_instance(**kwargs)
        return self.instance

    def create_by_vendor(
        self,
        api_key: str,
        vendor: AIVendor.LITERALS,
    ) -> AIProvider:

        """ Creates the provider with the name and the base url
            of a known vendor.

            Params:
              api_key: 'sk-proj-...'
              vendor: 'openai'

            Result:
              <AIProvider 'OpenAI'> with the base url
              'https://api.openai.com/v1' """

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

        """ Updates the provider, encrypts a new API key and drops
            the cached models when the credentials change.

            Params:
              force_save: True, saves the provider right away
              update_kwargs: {'name': 'OpenAI prod', 'api_key': 'sk-...'}

            Result:
              <AIProvider 'OpenAI prod'>, the models cache is cleared """

        credentials_changed = bool(
            {'api_key', 'base_url'} & update_kwargs.keys(),
        )
        if 'api_key' in update_kwargs:
            update_kwargs['api_key_encrypted'] = self.encrypt(
                update_kwargs.pop('api_key'),
            )
        super().partial_update(
            force_save=force_save,
            **update_kwargs,
        )
        if credentials_changed:
            self._delete_cache(key=self.instance.id)
        return self.instance

    def delete(self) -> None:

        """ Deletes the provider along with its cached models.

            Params:
              no params, the provider is self.instance <AIProvider 3>

            Result:
              None, the provider is deleted

            Raises:
              AIProviderInUseException: an agent still uses
                the provider """

        if self.instance.ai_agents.exists():
            raise AIProviderInUseException
        self._delete_cache(key=self.instance.id)
        super().delete()

    def _get_vendor(self):

        """ Vendor whose config is used to talk to the provider,
            a custom provider is treated as OpenAI compatible.

            Params:
              no params, the vendor is taken from self.instance

            Result:
              'anthropic' for an Anthropic provider,
              'openai' for a custom one """

        if self.instance.vendor == AIVendor.CUSTOM:
            return AIVendor.OPENAI
        return self.instance.vendor

    def _create_first_completion(self, models: List[dict]):

        """ Checks the provider with a test request to its models
            one by one. A model access error (403) or an empty response
            moves on to the next model, any other error stops the check.

            Params:
              models: [{'name': 'GPT-4o', 'slug': 'openai/gpt-4o'},
                {'name': 'GPT-4o mini', 'slug': 'openai/gpt-4o-mini'}]

            Result:
              'Hello world', the answer of the first model that responded

            Raises:
              AIProviderException: a model failed with a non-403 error,
                the next models are not requested
              AIProviderModelsNotResponded: every model is forbidden
                or answers with an empty response """

        handler = self._get_handler()
        for model in models:
            try:
                response = handler.get_completion(
                    system_message='You are a office employee.',
                    user_message='Say "Hello world"',
                    model=model['slug'],
                )
            except AIHandlerPermissionDenied:
                continue
            except AIHandlerUnauthorized as ex:
                raise AIProviderException(message=ex.message) from ex
            except AIHandlerException as ex:
                raise AIProviderException(
                    message=MSG_AI_0007(error=ex.message),
                ) from ex
            if not response:
                continue
            return response
        raise AIProviderModelsNotResponded

    def _get_handler(
        self,
        agent: Optional[AIAgent] = None,
        task: Optional[Task] = None,
    ) -> BaseHandler:

        """ Builds the vendor handler for the requests to the provider.

            Params:
              agent: <AIAgent 'Operator'>, a failed request is logged
                as its action 'request_failed'
              task: <Task 42>, the task the failed request is logged for

            Result:
              <OpenAIHandler> for an OpenAI or a custom provider """

        config = AI_VENDORS_CONFIG[self._get_vendor()]
        handler_cls = config['handler']
        return handler_cls(
            provider=self.instance,
            account=self.account,
            config=config,
            agent=agent,
            task=task,
        )

    def get_models(self) -> List[dict]:

        """ Models available to the provider, cached for a day
            for a saved provider.

            Params:
              no params, the provider is self.instance <AIProvider 3>

            Result:
              [{'name': 'GPT-4o', 'slug': 'openai/gpt-4o'}]

            Raises:
              AIProviderException: the provider is unavailable,
                rejected the request or returned an empty list """

        models = None
        if self.instance.id:
            models = self._get_cache(key=self.instance.id, default=[])
        if not models:
            handler = self._get_handler()
            try:
                models = handler.get_models()
            except (AIHandlerPermissionDenied, AIHandlerUnauthorized) as ex:
                raise AIProviderException(message=ex.message) from ex
            except AIHandlerException as ex:
                raise AIProviderException(
                    message=MSG_AI_0006(error=ex.message),
                ) from ex
            if not models:
                raise AIProviderException(
                    message=MSG_AI_0006(error='empty list'),
                )
            self._set_cache(key=self.instance.id, value=models)
        return models

    def get_completion(
        self,
        system_message: str,
        user_message: str,
        model: str,
        agent: Optional[AIAgent] = None,
        task: Optional[Task] = None,
    ) -> str:

        """ Sends a chat request to the provider model.

            Params:
              system_message: 'You are a office employee.'
              user_message: 'Say "Hello world"'
              model: 'openai/gpt-4o'
              agent: <AIAgent 'Operator'>, a failed request is logged
                as its action 'request_failed'
              task: <Task 42>, the task the failed request is logged for

            Result:
              'Hello world'

            Raises:
              AIProviderException: the provider is unavailable
                or rejected the request """

        handler = self._get_handler(agent=agent, task=task)
        try:
            return handler.get_completion(
                system_message=system_message,
                user_message=user_message,
                model=model,
            )
        except (AIHandlerPermissionDenied, AIHandlerUnauthorized) as ex:
            raise AIProviderException(message=ex.message) from ex
        except AIHandlerException as ex:
            raise AIProviderException(
                message=MSG_AI_0007(error=ex.message),
            ) from ex
