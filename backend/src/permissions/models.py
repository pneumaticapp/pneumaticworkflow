from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from guardian.managers import GroupObjectPermissionManager

from src.accounts.models import UserGroup


class GroupObjectPermission(models.Model):
    """
    Custom GroupObjectPermission model to avoid conflicts with guardian's.
    """
    class Meta:
        indexes = [
            models.Index(
                fields=['group', 'permission', 'content_type', 'object_pk'],
                name='perm_grp_perm_ct_obj_idx',
            ),
            models.Index(
                fields=['group', 'content_type', 'object_pk'],
                name='perm_grp_ct_obj_idx',
            ),
        ]
        unique_together = ['group', 'permission', 'object_pk']

    group = models.ForeignKey(
        UserGroup,
        on_delete=models.CASCADE,
        related_name='custom_group_permissions',
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name='custom_group_permissions',
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='custom_group_permissions',
    )
    object_pk = models.CharField(max_length=255)
    content_object = GenericForeignKey('content_type', 'object_pk')
    objects = GroupObjectPermissionManager()

    def __str__(self) -> str:
        return (
            f"{self.content_object} | {self.group} | "
            f"{self.permission.codename}"
        )
