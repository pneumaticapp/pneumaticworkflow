from django.contrib.auth import get_user_model
from django.db import IntegrityError

from src.generics.base.service import BaseModelService

from src.datasets.models import DatasetItem
from src.datasets.exceptions import DataSetServiceException
from src.datasets.messages import (
    MSG_DS_0002,
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
                message=MSG_DS_0002(value=value),
            ) from ex
        return self.instance

    def _create_related(self, **kwargs):
        pass

    def partial_update(
        self,
        force_save: bool = True,
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
                    message=MSG_DS_0002(value=self.instance.value),
                ) from ex
        return self.instance

    def delete(self) -> None:
        self.instance.delete()
