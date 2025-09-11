from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.db import models

from src.generics.managers import BaseSoftDeleteManager
from src.generics.models import SoftDeleteModel
from src.processes.querysets import (
    SystemTemplateQuerySet,
    SystemWorkflowKickoffDataQuerySet,
    SystemTemplateCategoryQuerySet,
)
from src.processes.enums import (
    SysTemplateType,
)
from django.contrib.postgres.search import SearchVectorField


UserModel = get_user_model()


class SystemTemplateCategory(SoftDeleteModel):

    class Meta:
        ordering = ('order',)
        verbose_name_plural = 'system template categories'

    is_active = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    name = models.CharField(max_length=64)
    icon = models.URLField(
        max_length=1024,
        null=True,
    )
    color = models.CharField(
        max_length=20,
        null=True,
        help_text='category color (hex)'
    )
    template_color = models.CharField(
        max_length=20,
        null=True,
        help_text='templates color (hex)'
    )
    objects = BaseSoftDeleteManager.from_queryset(
        SystemTemplateCategoryQuerySet
    )()

    def __str__(self):
        return self.name


class SystemTemplate(SoftDeleteModel):

    class Meta:
        ordering = ('name',)

    is_active = models.BooleanField(default=False)
    name = models.CharField(max_length=64)
    description = models.TextField(
        null=True,
        blank=True
    )
    template = JSONField(
        null=True,
        blank=True,
        help_text=(
            '<span style="float: right; line-height: 18px; '
            'font-size: 15px; color: #4C4C4C">'
            'If you want to pass default args to kickoff fields, add default '
            'parameter to field template like this: '
            '`"default": "account_name"`. <br>'
            'If you want to make generic name, you should add parameter '
            '"generic_name" like this: '
            '`"generic_name": "{{user_first_name}}\'s onboarding".<br>'
            'Possible dynamic values: '
            'account_name, user_first_name, user_last_name, user_email</span>'
        )
    )
    type = models.CharField(
        choices=SysTemplateType.CHOICES,
        default=SysTemplateType.LIBRARY,
        max_length=48
    )
    category = models.ForeignKey(
        SystemTemplateCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='for type "library"'
    )

    search_content = SearchVectorField(null=True)

    objects = BaseSoftDeleteManager.from_queryset(SystemTemplateQuerySet)()

    def __str__(self):
        return self.name


class SystemWorkflowKickoffData(SoftDeleteModel):

    """ Workflows launched after user registration """

    class Meta:
        ordering = ('user_role', 'order')
        verbose_name = 'System workflow kickoff'
        verbose_name_plural = 'System workflow kickoff'

    is_active = models.BooleanField(default=False)
    name = models.CharField(max_length=255)
    system_template = models.ForeignKey(
        SystemTemplate,
        on_delete=models.CASCADE,
        limit_choices_to={
            'type': SysTemplateType.ACTIVATED,
            'is_active': True
        },
        related_name='system_workflow_kickoff_data'
    )
    user_role = models.CharField(
        choices=SysTemplateType.ONBOARDING_CHOICES,
        max_length=255
    )
    order = models.IntegerField(default=0)
    kickoff_data = JSONField(
        null=True,
        blank=True,
        help_text=(
            '<span style="float: right; line-height: 18px; '
            'font-size: 15px; color: #4C4C4C">'
            'You can use template vars: <b>account_name, user_first_name, '
            'user_last_name, user_email</b></br>'
            'Example: Onboarding {{ user_first_name }} {{ user_first_name }}'
            '</span>'
        )
    )

    objects = BaseSoftDeleteManager.from_queryset(
        SystemWorkflowKickoffDataQuerySet
    )()
