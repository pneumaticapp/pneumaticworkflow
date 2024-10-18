from abc import abstractmethod
from django.db.models import Model
from django.contrib.auth import get_user_model
from pneumatic_backend.generics.base.service import BaseModelService
from pneumatic_backend.authentication.enums import (
    AuthTokenType
)

UserModel = get_user_model()


class BaseWorkflowService(BaseModelService):

    """ Represents common methods for workflow entities """

    @abstractmethod
    def _create_instance(
        self,
        instance_template: Model,
        **kwargs
    ):
        pass

    @abstractmethod
    def _create_related(
        self,
        instance_template: Model,
        **kwargs
    ):
        pass


class BaseUpdateVersionService:

    def __init__(
        self,
        user: UserModel,
        auth_type: AuthTokenType,
        is_superuser: bool,
        instance: Model = None,
        sync: bool = False
    ):
        self.user = user
        self.instance = instance
        self.sync = sync
        self.is_superuser = is_superuser
        self.auth_type = auth_type

    @abstractmethod
    def update_from_version(
        self,
        data: dict,
        version: int,
        **kwargs,
    ):
        pass
