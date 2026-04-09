from django.db import models
from django.db.models import Q, UniqueConstraint

from src.accounts.models import AccountBaseMixin
from src.generics.managers import BaseSoftDeleteManager
from src.generics.models import SoftDeleteModel
from src.processes.enums import FieldSetRuleType
from src.processes.querysets import (
    FieldsetTemplateQuerySet,
    FieldsetTemplateRuleQuerySet,
)


class FieldsetTemplate(SoftDeleteModel, AccountBaseMixin):

    class Meta:
        ordering = ['-id']
        constraints = [
            UniqueConstraint(
                fields=['account', 'name'],
                condition=Q(is_deleted=False),
                name='fieldsettemplate_account_name_unique',
            ),
        ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    date_created = models.DateTimeField(auto_now_add=True)

    objects = BaseSoftDeleteManager.from_queryset(
        FieldsetTemplateQuerySet,
    )()

    def __str__(self):
        return self.name


class FieldsetTemplateRule(SoftDeleteModel, AccountBaseMixin):

    class Meta:
        ordering = ['-id']

    name = models.CharField(max_length=200)
    type = models.CharField(
        max_length=50,
        choices=FieldSetRuleType.CHOICES,
        default=FieldSetRuleType.SUM_MAX,
    )
    value = models.TextField(blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    fieldset = models.ForeignKey(
        FieldsetTemplate,
        on_delete=models.CASCADE,
        related_name='rules',
    )

    objects = BaseSoftDeleteManager.from_queryset(
        FieldsetTemplateRuleQuerySet,
    )()

    def __str__(self):
        return self.name
