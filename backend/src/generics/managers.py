from django.db.models import Manager

from src.generics.mixins.managers import NormalizeEmailMixin


class BaseSoftDeleteManager(NormalizeEmailMixin, Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)
