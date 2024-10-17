from typing import Optional
from abc import abstractmethod
from django.db.models import Model
from django.db import transaction
from django.contrib.auth import get_user_model
from pneumatic_backend.authentication.enums import AuthTokenType


UserModel = get_user_model()


class BaseModelService:

    def __init__(
        self,
        user: Optional[UserModel] = None,
        instance=None,
        is_superuser: bool = False,
        auth_type: AuthTokenType.LITERALS = AuthTokenType.USER
    ):
        if user:
            self.user = user
            self.account = user.account
        else:
            self.user = None,
            self.account = None
        self.is_superuser = is_superuser
        self.auth_type = auth_type
        self.instance = instance
        self.update_fields = set()

    @abstractmethod
    def _create_related(
        self,
        **kwargs
    ):
        pass

    @abstractmethod
    def _create_instance(
        self,
        **kwargs
    ):

        pass

    def _create_actions(
        self,
        **kwargs
    ):
        pass

    def create(
        self,
        **kwargs
    ) -> Model:
        with transaction.atomic():
            self._create_instance(**kwargs)
            self._create_related(**kwargs)
            self._create_actions(**kwargs)
        return self.instance

    def save(self):
        if self.update_fields:
            self.instance.save(update_fields=list(self.update_fields))
            self.update_fields.clear()

    def partial_update(
        self,
        force_save=False,
        **update_kwargs
    ) -> Model:

        self.update_fields.update(update_kwargs.keys())
        for field_name, value in update_kwargs.items():
            setattr(self.instance, field_name, value)
        if force_save:
            self.save()
        return self.instance
