from django.db import models

from src.accounts.models import AccountBaseMixin
from src.generics.managers import BaseSoftDeleteManager
from src.generics.models import SoftDeleteModel
from src.processes.querysets import DatasetItemQuerySet, DatasetQuerySet


class Dataset(SoftDeleteModel, AccountBaseMixin):

    class Meta:
        ordering = ['-id']

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    date_created = models.DateTimeField(auto_now_add=True)

    objects = BaseSoftDeleteManager.from_queryset(DatasetQuerySet)()

    def __str__(self):
        return self.name


class DatasetItem(SoftDeleteModel):

    class Meta:
        ordering = ['order', 'id']

    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        related_name='items',
    )
    value = models.CharField(max_length=200)
    order = models.IntegerField(default=0)

    objects = BaseSoftDeleteManager.from_queryset(DatasetItemQuerySet)()

    def __str__(self):
        return self.value
