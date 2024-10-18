from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import (
    ValidationError as ValidationCoreError,
)
from django.db import models

from pneumatic_backend.generics.managers import BaseSoftDeleteManager
from pneumatic_backend.processes.messages.workflow import (
    MSG_PW_0059,
    MSG_PW_0060,
    MSG_PW_0061,
    MSG_PW_0062,
    MSG_PW_0063,
    MSG_PW_0064,
    MSG_PW_0065,
    MSG_PW_0068,
)
from pneumatic_backend.generics.models import SoftDeleteModel
from pneumatic_backend.processes.querysets import (
    SystemTemplateQuerySet,
    SystemWorkflowKickoffDataQuerySet,
    SystemTemplateCategoryQuerySet,
)
from pneumatic_backend.processes.utils.common import (
    VAR_PATTERN,
    is_tasks_ordering_correct,
)
from pneumatic_backend.processes.enums import (
    FieldType,
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

    def clean(self):
        if self.is_active:
            self.validate_template()

    def validate_template(self):

        # TODO move to serializer

        fields_to_check = []
        kickoff_api_names = set()

        kickoff = self.template.get('kickoff')
        if kickoff is not None:
            if not isinstance(kickoff, dict):
                raise ValidationCoreError(MSG_PW_0061)
            if kickoff.get('id'):
                raise ValidationCoreError(MSG_PW_0059)
            kickoff_fields = kickoff.get('fields')
            if kickoff_fields is not None:
                if not isinstance(kickoff_fields, list):
                    raise ValidationCoreError(MSG_PW_0062)
                fields_to_check.extend(kickoff['fields'])
                kickoff_api_names = self._get_kickoff_api_names(kickoff)

        tasks_numbers = []
        tasks = self.template.get('tasks')
        tasks = sorted(tasks, key=lambda i: i['number'])
        numbers = [task['number'] for task in tasks]

        if not is_tasks_ordering_correct(numbers):
            raise ValidationCoreError(MSG_PW_0063)
        for task in tasks:
            if task.get('id'):
                raise ValidationCoreError(MSG_PW_0059)
            if task['number'] == 1:
                if task.get('delay') is not None:
                    raise ValidationCoreError(MSG_PW_0068)
            if task.get('fields'):
                fields_to_check.extend(task['fields'])

            if not task.get('description'):
                continue

            api_names = [
                api_name
                for api_name in VAR_PATTERN.findall(task['description'])
            ]
            if not api_names:
                continue

            available_tasks = tasks[:task['number']-1]

            available_api_names = self._get_available_api_names(
                tasks=available_tasks,
                kickoff_api_names=kickoff_api_names,
            )

            invalid_api_names = list(set(api_names) - available_api_names)
            if invalid_api_names:
                tasks_numbers.append(task['number'])
        if tasks_numbers:
            raise ValidationCoreError(MSG_PW_0064(tasks_numbers))

        for field in fields_to_check:
            if field.get('id'):
                raise ValidationCoreError(MSG_PW_0059)
            if field.get('api_name') is None:
                raise ValidationCoreError(MSG_PW_0065)
            if field['type'] in [
                FieldType.RADIO,
                FieldType.CHECKBOX,
                FieldType.DROPDOWN
            ]:
                if not field.get('selections'):
                    raise ValidationCoreError(MSG_PW_0060)

    def _get_kickoff_api_names(self, kickoff, field_type=None):
        try:
            return set(
                field['api_name'] for field in kickoff['fields']
                if field_type is None or field['type'] == field_type
            )
        except KeyError:
            raise ValidationCoreError(MSG_PW_0065)

    def _get_available_api_names(
        self,
        tasks,
        kickoff_api_names,
        field_type=None,
    ):
        try:
            return kickoff_api_names.union(
                field['api_name'] for available_task in tasks
                for field in available_task.get('fields', [])
                if field_type is None or field['type'] == field_type
            )
        except KeyError:
            raise ValidationCoreError(MSG_PW_0065)

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
