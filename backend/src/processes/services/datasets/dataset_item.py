from django.contrib.auth import get_user_model
from django.db import IntegrityError

from src.generics.base.service import BaseModelService

from src.processes.models.dataset import DatasetItem
from src.processes.services.exceptions import (
    DataSetServiceException,
)
from src.processes.messages.workflow import (
    MSG_PW_0093,
)


UserModel = get_user_model()


class DataSetItemService(BaseModelService):

    def _create_instance(
        self,
        dataset_id: int,
        value: str,
        order: int,
    ):
        try:
            self.instance = DatasetItem.objects.create(
                account_id=self.account.id,
                dataset_id=dataset_id,
                value=value,
                order=order,
            )
        except IntegrityError as ex:
            raise DataSetServiceException(
                message=MSG_PW_0093(value=value),
            ) from ex
        return self.instance

    def _create_related(self, **kwargs):
        pass

    def partial_update(
        self,
        force_save=False,
        **update_kwargs,
    ) -> DatasetItem:

        self.update_fields.update(update_kwargs.keys())
        for field_name, value in update_kwargs.items():
            setattr(self.instance, field_name, value)
        if force_save:
            try:
                self.save()
            except IntegrityError as ex:
                raise DataSetServiceException(
                    message=MSG_PW_0093(value=self.instance.value),
                ) from ex
        return self.instance

    def delete(self) -> None:
        self.instance.delete()
