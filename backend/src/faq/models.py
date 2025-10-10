from django.db.models import (
    TextField,
    BooleanField,
    PositiveIntegerField,
)
from src.generics.models import SoftDeleteModel
from src.faq.querysets import FaqItemQuerySet


class FaqItem(SoftDeleteModel):

    class Meta:
        ordering = ('order',)
        verbose_name = 'Item'

    is_active = BooleanField(default=False)
    order = PositiveIntegerField(default=1)
    question = TextField()
    answer = TextField()

    objects = FaqItemQuerySet.as_manager()

    def __str__(self):
        return self.question[:100]
