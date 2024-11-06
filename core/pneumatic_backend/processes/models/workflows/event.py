from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import (
    ArrayField,
    JSONField,
)
from django.db import models
from django.contrib.postgres.search import SearchVectorField

from pneumatic_backend.processes.querysets import (
    WorkflowEventQuerySet,
    WorkflowEventActionQuerySet,
)
from pneumatic_backend.generics.managers import BaseSoftDeleteManager
from pneumatic_backend.processes.models import Workflow, Task
from pneumatic_backend.processes.enums import (
    WorkflowEventType,
    WorkflowEventActionType,
    CommentStatus,
)
from pneumatic_backend.accounts.models import AccountBaseMixin
from pneumatic_backend.generics.models import SoftDeleteModel

UserModel = get_user_model()


class WorkflowEvent(
    SoftDeleteModel,
    AccountBaseMixin
):

    class Meta:
        ordering = ('-created',)

    type = models.IntegerField(
        choices=WorkflowEventType.CHOICES,
        verbose_name='type'
    )
    status = models.CharField(
        default=CommentStatus.CREATED,
        choices=CommentStatus.CHOICES,
        max_length=20
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(null=True)
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='events',
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.SET_NULL,
        related_name='events',
        null=True,
        help_text='Not null for task events and comments'
    )
    task_json = JSONField(null=True)
    text = models.TextField(blank=True, null=True)
    clear_text = models.TextField(blank=True, null=True)
    user = models.ForeignKey(
        UserModel,
        on_delete=models.SET_NULL,
        null=True,
    )
    delay_json = JSONField(null=True)
    watched = ArrayField(JSONField(), default=list)
    reactions = JSONField(default=dict)
    target_user_id = models.IntegerField(null=True)
    with_attachments = models.BooleanField(default=False)
    search_content = SearchVectorField(null=True)

    objects = BaseSoftDeleteManager.from_queryset(WorkflowEventQuerySet)()


class WorkflowEventAction(
    SoftDeleteModel,
):

    """ Marks that workflow event has new watched or reactions actions """

    created = models.DateTimeField(auto_now_add=True)
    event = models.ForeignKey(
        WorkflowEvent,
        on_delete=models.CASCADE,
        related_name='actions',
    )
    user = models.ForeignKey(
        UserModel,
        on_delete=models.SET_NULL,
        null=True,
    )
    type = models.IntegerField(choices=WorkflowEventActionType.CHOICES)
    objects = BaseSoftDeleteManager.from_queryset(
        WorkflowEventActionQuerySet
    )()
