from typing import Optional
from django.contrib.auth import get_user_model
from src.ai.models import AIAgent
from src.generics.base.service import BaseModelService

UserModel = get_user_model()


class AIAgentService(BaseModelService):

    def _create_instance(
        self,
        name: str,
        model: str,
        is_active: bool = True,
        system_prompt: str = '',
        photo: Optional[str] = None,
        provider_id: Optional[int] = None,
        **kwargs,
    ):
        pass

    def partial_update(
        self,
        **update_kwargs,
    ) -> AIAgent:
        pass

    def delete(self) -> None:
        pass
