from django.db.models import UniqueConstraint, Q
from rest_hooks.models import AbstractHook

from pneumatic_backend.accounts.models import AccountBaseMixin
from pneumatic_backend.generics.managers import BaseSoftDeleteManager
from pneumatic_backend.generics.models import SoftDeleteModel
from pneumatic_backend.webhooks.querysets import WebHookQuerySet


# pylint: disable=W
class WebHook(SoftDeleteModel, AbstractHook, AccountBaseMixin):
    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['account', 'target', 'event'],
                condition=Q(is_deleted=False),
                name='webhook_unique_constraint',
            )
        ]

    objects = BaseSoftDeleteManager.from_queryset(WebHookQuerySet)()

    def __str__(self):
        return f'{self.event} —> {self.target}'
