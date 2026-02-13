# ruff: noqa: PLC0415 UP031
from copy import deepcopy
from typing import List

from django.contrib.auth import get_user_model
from rest_framework.serializers import ValidationError

from src.accounts.models import UserGroup
from src.analysis.services import AnalyticService
from src.generics.base.service import BaseModelService
from src.processes.enums import (
    OwnerType,
    PerformerType,
    sys_template_type_map,
)
from src.processes.models.templates.fields import FieldTemplate
from src.processes.models.templates.system_template import SystemTemplate
from src.processes.models.templates.task import TaskTemplate
from src.processes.models.templates.template import Template
from src.processes.utils.common import (
    create_api_name,
    insert_fields_values_to_text,
)
from src.storage.utils import refresh_attachments
from src.utils.logging import (
    SentryLogLevel,
    capture_sentry_message,
)

UserModel = get_user_model()


class TemplateService(BaseModelService):

    def _create_related(
        self,
        **kwargs,
    ):
        # Update attachments for template
        if self.instance:
            refresh_attachments(self.instance, self.user)

    def _create_instance(
        self,
        **kwargs,
    ):
        pass

    def partial_update(
        self,
        force_save=False,
        **update_kwargs,
    ) -> Template:
        result = super().partial_update(
            force_save=force_save,
            **update_kwargs,
        )
        if 'description' in update_kwargs and self.instance:
            refresh_attachments(self.instance, self.user)
        return result

    def fill_template_data(self, initial_data: dict) -> dict:

        """ initial_data - known template data,
            returns full data based on known data"""

        initial_kickoff_data = initial_data.get('kickoff', {})
        initial_tasks_data = initial_data.get('tasks', [])
        data = {
            'name': initial_data.get('name', ''),
            'wf_name_template': initial_data.get('wf_name_template'),
            'description': initial_data.get('description', ''),
            'is_active': initial_data.get('is_active', False),
            'finalizable': initial_data.get('finalizable', True),
            'is_public': initial_data.get('is_public', False),
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': f'{self.user.id}',
                },
            ],
            'kickoff': {
                'description': initial_kickoff_data.get('description', ''),
                'fields': initial_kickoff_data.get('fields', []),
            },
            'tasks': deepcopy(initial_tasks_data),
        }

        fields_values = {}
        for field_data in data['kickoff']['fields']:
            api_name = field_data.get('api_name')
            if api_name:
                fields_values[api_name] = '{{%s}}' % api_name
            else:
                field_data['api_name'] = create_api_name(
                    prefix=FieldTemplate.api_name_prefix,
                )
        for task_data in data['tasks']:
            task_data['api_name'] = task_data.get(
                'api_name',
                create_api_name(prefix=TaskTemplate.api_name_prefix),
            )
            raw_performers = task_data.get('raw_performers')
            if not raw_performers:
                task_data['raw_performers'] = [
                    {
                        'type': PerformerType.USER,
                        'source_id': self.user.id,
                        'label': self.user.name,
                    },
                ]
            task_fields = task_data.get('fields', [])
            for field_data in task_fields:
                api_name = field_data.get('api_name')
                if api_name:
                    fields_values[api_name] = '{{%s}}' % api_name
                else:
                    field_data['api_name'] = create_api_name(
                        prefix=TaskTemplate.api_name_prefix,
                    )
            if task_data.get('description'):
                task_data['description'] = insert_fields_values_to_text(
                    text=task_data['description'],
                    fields_values=fields_values,
                )
        return data

    def get_from_sys_template(
        self,
        sys_template: SystemTemplate,
    ) -> dict:

        data = self.fill_template_data(
            initial_data=sys_template.template,
        )
        AnalyticService.library_template_opened(
            user=self.user,
            sys_template=sys_template,
            auth_type=self.auth_type,
            is_superuser=self.is_superuser,
        )
        return data

    def create_template_by_steps(
        self,
        name: str,
        tasks: List[dict],
    ) -> Template:

        data = self.fill_template_data(
            initial_data={
                'name': name,
                'is_active': True,
                'tasks': tasks,
            },
        )
        from src.processes.serializers.templates.template import (
            TemplateSerializer,
        )
        slz = TemplateSerializer(
            data=data,
            context={
                'user': self.user,
                'account': self.account,
                'is_superuser': self.is_superuser,
                'auth_type': self.auth_type,
            },
        )
        try:
            slz.is_valid(raise_exception=True)
            self.instance = slz.save()
        except ValidationError as ex:
            capture_sentry_message(
                message=f'Create template by steps failed ({self.account.id})',
                level=SentryLogLevel.ERROR,
                data={
                    'initial_data': data,
                    'error': ex,
                },
            )
            raise
        else:
            AnalyticService.template_generated_from_landing(
                template=self.instance,
                user=self.user,
                auth_type=self.auth_type,
                is_superuser=self.is_superuser,
            )
            return self.instance

    def create_template_from_sys_template(
        self,
        system_template: SystemTemplate,
    ) -> Template:

        """ Create template from system_template data """

        template_data: dict = deepcopy(system_template.template)
        template_data['kickoff'] = template_data.get('kickoff', {})
        template_data['tasks'] = template_data.get('tasks', [])
        template_data['name'] = insert_fields_values_to_text(
            text=template_data.get('name', ''),
            fields_values=self.user.get_dynamic_mapping(),
        )
        user_owners = [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
            }
            for user in
            UserModel.objects.on_account(self.account.id).order_by('id')
        ]
        group_owners = [
            {
                'type': OwnerType.GROUP,
                'source_id': group.id,
            }
            for group in
            UserGroup.objects.filter(account_id=self.account.id).order_by('id')
        ]
        template_data['owners'] = user_owners + group_owners
        template_data['is_active'] = True

        for task_data in template_data['tasks']:
            if not task_data.get('api_name'):
                task_data['api_name'] = create_api_name(prefix='task')
            if not task_data.get('raw_performers'):
                task_data['raw_performers'] = [
                    {
                        'type': PerformerType.USER,
                        'source_id': self.user.id,
                    },
                ]

        generic_name = template_data.pop('generic_name', None)
        template_type = sys_template_type_map[system_template.type]

        # TemplateSerializer does not support 'type' and 'generic_name' fields,
        # for this reason the fields are passed through the form context
        from src.processes.serializers.templates.template import (
            TemplateSerializer,
        )
        template_slz = TemplateSerializer(
            data=template_data,
            context={
                'account': self.account,
                'user': self.user,
                'type': template_type,
                'generic_name': generic_name,
                'is_superuser': False,
                'auth_type': self.auth_type,
                'automatically_created': True,
            },
        )
        try:
            template_slz.is_valid(raise_exception=True)
            template = template_slz.save()
        except ValidationError:
            template = template_slz.save_as_draft()
        template.system_template_id = system_template.id
        template.save(update_fields=['system_template_id'])
        return template

    def create_template_from_library_template(
        self,
        system_template: SystemTemplate,
    ) -> Template:

        template = self.create_template_from_sys_template(
            system_template=system_template,
        )
        AnalyticService.template_created_from_landing_library(
            user=self.user,
            template=template,
            auth_type=self.auth_type,
            is_superuser=self.is_superuser,
        )
        return template
