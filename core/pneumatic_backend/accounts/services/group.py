from typing import List, Optional
from pneumatic_backend.generics.base.service import BaseModelService
from pneumatic_backend.accounts.models import UserGroup
from django.db import IntegrityError
from pneumatic_backend.accounts.services.exceptions import (
    AlreadyRegisteredException,
)


class UserGroupService(BaseModelService):

    def _create_instance(
        self,
        name: str,
        photo: Optional[str] = None,
        users: Optional[List[int]] = None,
        **kwargs
    ):
        try:
            self.instance = UserGroup.objects.create(
                name=name,
                photo=photo,
                account=self.account,
            )
        except IntegrityError:
            raise AlreadyRegisteredException()
        return self.instance

    def _create_related(
        self,
        users: Optional[List[int]] = None,
        **kwargs
    ):
        if users:
            self.instance.users.set(users)

    def partial_update(
        self,
        force_save=False,
        **update_kwargs
    ):
        users = update_kwargs.pop('users', None)
        if isinstance(users, list):
            if users:
                self.instance.users.set(users)
            else:
                self.instance.users.clear()
        return super().partial_update(
            **update_kwargs,
            force_save=force_save
        )
