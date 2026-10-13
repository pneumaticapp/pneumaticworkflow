from typing import Dict, List, Optional

from django.contrib.auth import get_user_model
from django.db import IntegrityError

from src.generics.base.service import BaseModelService
from src.notifications.tasks import (
    send_dataset_created_notification,
    send_dataset_deleted_notification,
    send_dataset_updated_notification,
)
from src.datasets.models import Dataset
from src.datasets.serializers import DatasetSerializer
from src.datasets.services.dataset_item import DataSetItemService
from src.datasets.exceptions import DataSetNameNotUniqueException

UserModel = get_user_model()


class DataSetService(BaseModelService):

    def _create_instance(
        self,
        name: str,
        description: str = '',
        **kwargs,
    ):
        try:
            self.instance = Dataset.objects.create(
                account=self.account,
                name=name,
                description=description,
            )
        except IntegrityError as ex:
            raise DataSetNameNotUniqueException from ex
        return self.instance

    def _create_related(
        self,
        items: Optional[List[Dict]] = None,
        **kwargs,
    ):
        if items:
            self.create_items(items_data=items)

    def _create_actions(self, **kwargs):
        send_dataset_created_notification.delay(
            logging=self.account.log_api_requests,
            account_id=self.account.id,
            dataset_data=DatasetSerializer(self.instance).data,
        )

    def partial_update(
        self,
        **update_kwargs,
    ) -> Dataset:

        items_data = update_kwargs.pop('items', None)
        try:
            result = super().partial_update(
                force_save=True,
                **update_kwargs,
            )
        except IntegrityError as ex:
            raise DataSetNameNotUniqueException from ex
        if items_data is not None:
            self.update_items(items_data=items_data)
        send_dataset_updated_notification.delay(
            logging=self.account.log_api_requests,
            account_id=self.account.id,
            dataset_data=DatasetSerializer(self.instance).data,
        )
        return result

    def delete(self) -> None:
        send_dataset_deleted_notification.delay(
            logging=self.account.log_api_requests,
            account_id=self.account.id,
            dataset_data=DatasetSerializer(self.instance).data,
        )
        self.instance.delete()

    def create_items(
        self,
        items_data: List[Dict],
    ):
        service = DataSetItemService(
            user=self.user,
            is_superuser=self.is_superuser,
            auth_type=self.auth_type,
        )
        for item_data in items_data:
            service.create(
                dataset_id=self.instance.id,
                **item_data,
            )

    def update_items(
        self,
        items_data: List[Dict],
    ):
        """ All dataset items will be updated """

        existing_items = {
            item.id: item
            for item in self.instance.items.all()
        }
        items_ids = set()
        for item_data in items_data:
            item_id = item_data.pop('id', None)
            if item_id and item_id in existing_items:
                service = DataSetItemService(
                    user=self.user,
                    is_superuser=self.is_superuser,
                    auth_type=self.auth_type,
                    instance=existing_items[item_id],
                )
                service.partial_update(**item_data)
                items_ids.add(item_id)
            else:
                service = DataSetItemService(
                    user=self.user,
                    is_superuser=self.is_superuser,
                    auth_type=self.auth_type,
                )
                dataset_item = service.create(
                    dataset_id=self.instance.id,
                    **item_data,
                )
                items_ids.add(dataset_item.id)

        self.instance.items.exclude(id__in=items_ids).delete()
