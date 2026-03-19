from typing import Any, Dict, List, Optional

from django.contrib.auth import get_user_model
from django.db import IntegrityError

from src.generics.base.service import BaseModelService
from src.processes.models.dataset import Dataset, DatasetItem
from src.processes.services.exceptions import (
    DataSetItemValueNotUniqueException,
    DataSetNameNotUniqueException,
)

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
        items: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ):
        if items:
            self._create_items(items_data=items)

    def partial_update(
        self,
        force_save: bool = False,
        **update_kwargs,
    ) -> Dataset:

        items = update_kwargs.pop('items', None)
        try:
            result = super().partial_update(
                force_save=force_save,
                **update_kwargs,
            )
        except IntegrityError as ex:
            raise DataSetNameNotUniqueException from ex
        if items is not None:
            self._update_items(items_data=items)
        return result

    def delete(self) -> None:
        self.instance.delete()

    def _create_items(
        self,
        items_data: List[Dict[str, Any]],
    ):
        items_to_create = [
            DatasetItem(
                dataset=self.instance,
                value=item_data['value'],
                order=item_data.get('order', 0),
            )
            for item_data in items_data
        ]
        try:
            DatasetItem.objects.bulk_create(items_to_create)
        except IntegrityError as ex:
            raise DataSetItemValueNotUniqueException from ex

    def _update_items(
        self,
        items_data: List[Dict[str, Any]],
    ):
        existing_items = {
            item.id: item
            for item in self.instance.items.all()
        }
        incoming_ids = set()
        items_to_create = []
        items_to_update = []

        for item_data in items_data:
            item_id = item_data.get('id')
            if item_id and item_id in existing_items:
                # Update existing item
                incoming_ids.add(item_id)
                item = existing_items[item_id]
                item.value = item_data['value']
                item.order = item_data.get('order', 0)
                items_to_update.append(item)
            else:
                # Create new item
                items_to_create.append(
                    DatasetItem(
                        dataset=self.instance,
                        value=item_data['value'],
                        order=item_data.get('order', 0),
                    ),
                )

        # Delete items not present in incoming data
        ids_to_delete = set(existing_items.keys()) - incoming_ids
        if ids_to_delete:
            self.instance.items.filter(id__in=ids_to_delete).delete()

        if items_to_update:
            try:
                DatasetItem.objects.bulk_update(
                    items_to_update,
                    fields=['value', 'order'],
                )
            except IntegrityError as ex:
                raise DataSetItemValueNotUniqueException from ex
        if items_to_create:
            try:
                DatasetItem.objects.bulk_create(items_to_create)
            except IntegrityError as ex:
                raise DataSetItemValueNotUniqueException from ex
