from src.ai.models import AIProvider
from src.generics.base.service import BaseModelService


class AIProviderService(BaseModelService):

    def _create_instance(
        self,
        name: str,
        base_url: str,
        api_key: str,
        is_active: bool = True,
        **kwargs,
    ):
        pass

    def partial_update(
        self,
        **update_kwargs,
    ) -> AIProvider:
        pass

    def delete(self) -> None:
        pass
