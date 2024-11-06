from django.contrib.auth import get_user_model
from django.db.models import (
    UniqueConstraint,
    Q,
    DateTimeField,
    ForeignKey,
    CharField,
    URLField,
    CASCADE
)
from pneumatic_backend.accounts.models import AccountBaseMixin
from pneumatic_backend.generics.managers import BaseSoftDeleteManager
from pneumatic_backend.generics.models import SoftDeleteModel
from pneumatic_backend.webhooks.querysets import WebHookQuerySet


UserModel = get_user_model()


class WebHook(SoftDeleteModel, AccountBaseMixin):

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['account', 'target', 'event'],
                condition=Q(is_deleted=False),
                name='webhook_unique_constraint',
            )
        ]

    created = DateTimeField(auto_now_add=True)
    updated = DateTimeField(auto_now=True)
    user = ForeignKey(
        UserModel,
        related_name='webhooks',
        on_delete=CASCADE
    )
    event = CharField('Event', max_length=64, db_index=True)
    target = URLField('Target URL', max_length=255)

    objects = BaseSoftDeleteManager.from_queryset(WebHookQuerySet)()

    def __str__(self):
        return f'{self.event} —> {self.target}'

    def dict(self):
        return {
            'id': self.id,
            'event': self.event,
            'target': self.target
        }
