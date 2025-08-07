from django.db.models import (
    Model,
    TextField,
    CharField,
)
from pneumatic_backend.pages.enums import PageType
from pneumatic_backend.pages.querysets import PageQuerySet


class Page(Model):

    class Meta:
        ordering = ('id',)

    slug = CharField(
        max_length=50,
        unique=True,
        choices=PageType.CHOICES
    )
    title = CharField(max_length=500)
    description = TextField(
        max_length=500,
        default='',
        blank=True
    )

    objects = PageQuerySet.as_manager()

    def __str__(self):
        return self.slug
