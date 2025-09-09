from django.db.models import Manager
from pneumatic_backend.generics.mixins.managers import NormalizeEmailMixin


class BaseSoftDeleteManager(NormalizeEmailMixin, Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)
