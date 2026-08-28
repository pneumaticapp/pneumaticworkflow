import string
from typing import Optional
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils.crypto import get_random_string

from src.accounts.services.user import UserService
from src.ai.exceptions import AIAgentNameNotUniqueException
from src.ai.models import AIAgent
from src.generics.base.service import BaseModelService

UserModel = get_user_model()


class AIAgentService(BaseModelService):

    def _get_agent_email(self) -> str:
        domain = self.account.get_owner().email.split('@')[1]
        salt = get_random_string(
            length=20,
            allowed_chars=string.ascii_letters + string.digits,
        )
        email = f'ai-agent-{salt}@{domain}'
        if UserModel.include_inactive.filter(email=email).exists():
            return self._get_agent_email()
        return email

    def _create_instance(
        self,
        name: str,
        model: str,
        system_prompt: str,
        is_active: bool = True,
        photo: Optional[str] = None,
        provider_id: Optional[int] = None,
        **kwargs,
    ):
        user_service = UserService(
            user=self.user,
            is_superuser=self.is_superuser,
            auth_type=self.auth_type,
        )
        with transaction.atomic():
            agent_user = user_service.create(
                account=self.account,
                email=self._get_agent_email(),
                first_name=name,
                photo=photo,
                is_admin=True,
                is_ai=True,
                is_tasks_digest_subscriber=False,
                is_digest_subscriber=False,
                is_newsletters_subscriber=False,
                is_special_offers_subscriber=False,
                is_new_tasks_subscriber=False,
                is_complete_tasks_subscriber=False,
                is_comments_mentions_subscriber=False,
            )
            try:
                self.instance = AIAgent.objects.create(
                    account=self.account,
                    name=name,
                    model=model,
                    is_active=is_active,
                    system_prompt=system_prompt,
                    photo=photo,
                    provider_id=provider_id,
                    user=agent_user,
                )
            except IntegrityError as ex:
                raise AIAgentNameNotUniqueException from ex
        return self.instance

    def partial_update(
        self,
        force_save=True,
        **update_kwargs,
    ) -> AIAgent:
        user_update = {}
        if 'name' in update_kwargs:
            user_update['first_name'] = update_kwargs['name']
        if 'photo' in update_kwargs:
            user_update['photo'] = update_kwargs['photo']
        with transaction.atomic():
            if user_update:
                UserService(
                    user=self.user,
                    instance=self.instance.user,
                    is_superuser=self.is_superuser,
                    auth_type=self.auth_type,
                ).partial_update(**user_update)
            try:
                result = super().partial_update(
                    force_save=force_save,
                    **update_kwargs,
                )
            except IntegrityError as ex:
                raise AIAgentNameNotUniqueException from ex
        return result

    def delete(self) -> None:
        pass
