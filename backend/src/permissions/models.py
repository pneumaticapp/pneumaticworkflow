from django.db import models
from guardian.models import (
    BaseObjectPermission,
    GroupObjectPermissionManager,
)

from src.accounts.models import UserGroup


class GroupObjectPermission(BaseObjectPermission):
    class Meta:
        indexes = [
            models.Index(
                fields=['group', 'permission', 'content_type', 'object_pk'],
            ),
            models.Index(fields=['group', 'content_type', 'object_pk']),
        ]
        unique_together = ['group', 'permission', 'object_pk']

    group = models.ForeignKey(UserGroup, on_delete=models.CASCADE)
    objects = GroupObjectPermissionManager()

    def __str__(self) -> str:
        return (
            f"{self.content_object} | {self.group} | "
            f"{self.permission.codename}"
        )
