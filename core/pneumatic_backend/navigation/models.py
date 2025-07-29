from django.db.models import (
    Model,
    CharField,
    ForeignKey,
    PositiveIntegerField,
    URLField,
    BooleanField,
    CASCADE
)
from pneumatic_backend.navigation.enums import MenuType


class Menu(Model):
    slug = CharField(
        max_length=50,
        unique=True,
        choices=MenuType.CHOICES
    )
    label = CharField(max_length=120)
    link = URLField(null=True, blank=True)

    def __str__(self):
        return self.label


class MenuItem(Model):
    class Meta:
        ordering = ('order',)

    menu = ForeignKey(
        Menu,
        on_delete=CASCADE,
        related_name='items'
    )
    label = CharField(max_length=120)
    link = URLField()
    order = PositiveIntegerField()
    show = BooleanField(default=True)

    def __str__(self):
        return self.label
