from django.db import models, transaction
from pneumatic_backend.generics.mixins.models import SoftDeleteMixin


class SoftDeleteModel(SoftDeleteMixin, models.Model):

    class Meta:
        abstract = True

    is_deleted = models.BooleanField(default=False)

    @transaction.atomic
    def delete(self, **kwargs):
        self.is_deleted = True
        update_fields = kwargs.pop('update_fields', [])
        update_fields.append('is_deleted')
        self._on_delete(**kwargs)
        self.save(update_fields=update_fields)
