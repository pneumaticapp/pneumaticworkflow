from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from guardian.managers import GroupObjectPermissionManager
from guardian.models import UserObjectPermissionAbstract

from src.accounts.models import UserGroup
from src.permissions.enums import PermissionSource


UserModel = get_user_model()


class UserObjectPermission(UserObjectPermissionAbstract):
    """Object-level permission with source tracking.

    Extends Guardian's ``UserObjectPermissionAbstract`` with ``source_type``
    and ``source_id`` for surgical revoke when a source is removed.

    Do NOT use ``assign_perm()`` / ``remove_perm()`` for workflows —
    use ``WorkflowPermissionService`` (source-aware).
    """

    class Meta(UserObjectPermissionAbstract.Meta):
        abstract = False
        unique_together = None
        indexes = [
            models.Index(
                fields=['source_type', 'source_id'],
                name='perm_uop_source_idx',
            ),
            models.Index(
                fields=[
                    'content_type', 'object_pk',
                    'source_type', 'source_id',
                ],
                name='perm_uop_ct_obj_source_idx',
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'user', 'permission', 'content_type', 'object_pk',
                    'source_type', 'source_id',
                ],
                name='perm_uop_unique',
            ),
        ]

    user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name='object_permissions',
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name='+',
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='+',
    )

    source_type = models.CharField(
        max_length=50,
        choices=PermissionSource.CHOICES,
        help_text='The model/entity that provided this permission.',
    )
    source_id = models.CharField(
        max_length=255,
        help_text='PK of the source entity.',
    )

    def __str__(self):
        return (
            f"user={self.user_id} | perm={self.permission_id} | "
            f"obj={self.object_pk} | {self.source_type}:{self.source_id}"
        )


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
        constraints = [
            models.UniqueConstraint(
                fields=['group', 'permission', 'content_type', 'object_pk'],
                name='perm_grp_unique',
            ),
        ]

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
            f"group={self.group_id} | perm={self.permission_id} | "
            f"ct={self.content_type_id} obj={self.object_pk}"
        )
