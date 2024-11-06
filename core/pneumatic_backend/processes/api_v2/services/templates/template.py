from typing import Optional, List
from copy import deepcopy
from collections import defaultdict
from django.contrib.auth import get_user_model

from pneumatic_backend.processes.models import (
    TaskTemplate,
    FieldTemplate,
    SystemTemplate,
)
from pneumatic_backend.processes.utils.common import create_api_name
from pneumatic_backend.processes.utils.common import (
    insert_fields_values_to_text
)
from pneumatic_backend.executor import RawSqlExecutor
from pneumatic_backend.processes.queries import (
    TemplateListQuery
)
from pneumatic_backend.processes.enums import (
    PerformerType,
    TemplateOrdering,
    sys_template_type_map,
)
from pneumatic_backend.processes.api_v2.serializers.template.kickoff import (
    KickoffListSerializer
)
from pneumatic_backend.processes.models import (
    Template,
    Kickoff
)
from pneumatic_backend.generics.base.service import BaseModelService
from rest_framework.serializers import ValidationError
from pneumatic_backend.utils.logging import (
    capture_sentry_message,
    SentryLogLevel
)
from pneumatic_backend.analytics.services import AnalyticService


UserModel = get_user_model()


class TemplateService(BaseModelService):

    def _create_related(
        self,
        **kwargs
    ):
        pass

    def _create_instance(
        self,
        **kwargs
    ):
        pass

    def get_templates_data(
        self,
        ordering: Optional[TemplateOrdering] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_public: Optional[bool] = None,
        is_template_owner: Optional[bool] = None,
    ) -> List[dict]:

        """ Returns list of filtered templates
            Adds kickoff and template_owners to the data
            through bulk selection """

        query = TemplateListQuery(
            user=self.user,
            account_id=self.account.id,
            ordering=ordering,
            search_text=search,
            is_active=is_active,
            is_public=is_public,
            is_template_owner=is_template_owner,
        )
        templates_data = []
        templates_ids = set()
        for row in RawSqlExecutor.fetch(*query.get_sql()):
            row['template_owners'] = []
            templates_data.append(row)
            templates_ids.add(row['id'])

        template_owners_dict = defaultdict(list)
        for template_owner in Template.template_owners.through.objects.filter(
            template_id__in=templates_ids
        ):
            template_owners_dict[template_owner.template_id].append(
                template_owner.user_id
            )

        kickoff_dict = {}
        for kickoff in Kickoff.objects.filter(
            template_id__in=templates_ids
        ).prefetch_related('fields__selections'):
            kickoff_dict[kickoff.template_id] = (
                KickoffListSerializer(
                    instance=kickoff
                ).data
            )

        for template_data in templates_data:
            template_data['template_owners'] = template_owners_dict[
                template_data['id']
            ]
            template_data['kickoff'] = kickoff_dict[template_data['id']]
        return templates_data

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
            'template_owners': [self.user.id],
            'tasks_count': len(initial_data.get('tasks', [])),
            'performers_count': 1,
            'kickoff': {
                'description': initial_kickoff_data.get('description', ''),
                'fields': initial_kickoff_data.get('fields', [])
            },
            'tasks': deepcopy(initial_tasks_data)
        }

        fields_values = {}
        for field_data in data['kickoff']['fields']:
            api_name = field_data.get('api_name')
            if api_name:
                fields_values[api_name] = '{{%s}}' % api_name
            else:
                field_data['api_name'] = create_api_name(
                    prefix=FieldTemplate.api_name_prefix
                )
        for task_data in data['tasks']:
            task_data['api_name'] = task_data.get(
                'api_name',
                create_api_name(prefix=TaskTemplate.api_name_prefix)
            )
            raw_performers = task_data.get('raw_performers')
            if not raw_performers:
                task_data['raw_performers'] = [
                    {
                        'type': PerformerType.USER,
                        'source_id': self.user.id,
                        'label': self.user.name
                    }
                ]
            task_fields = task_data.get('fields', [])
            for field_data in task_fields:
                api_name = field_data.get('api_name')
                if api_name:
                    fields_values[api_name] = '{{%s}}' % api_name
                else:
                    field_data['api_name'] = create_api_name(
                        prefix=TaskTemplate.api_name_prefix
                    )
            if task_data.get('description'):
                task_data['description'] = insert_fields_values_to_text(
                    text=task_data['description'],
                    fields_values=fields_values
                )
        return data

    def get_from_sys_template(
        self,
        sys_template: SystemTemplate
    ) -> dict:

        data = self.fill_template_data(
            initial_data=sys_template.template
        )
        AnalyticService.library_template_opened(
            user=self.user,
            sys_template=sys_template,
            auth_type=self.auth_type,
            is_superuser=self.is_superuser
        )
        return data

    def create_template_by_steps(
        self,
        name: str,
        tasks: List[dict]
    ) -> Template:

        data = self.fill_template_data(
            initial_data={
                'name': name,
                'is_active': True,
                'tasks': tasks
            }
        )
        from pneumatic_backend.processes.api_v2.serializers.\
            template.template import TemplateSerializer
        slz = TemplateSerializer(
            data=data,
            context={
                'user': self.user,
                'account': self.account,
                'is_superuser': self.is_superuser,
                'auth_type': self.auth_type
            }
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
                    'error': ex
                }
            )
            raise
        else:
            AnalyticService.template_generated_from_landing(
                template=self.instance,
                user=self.user,
                auth_type=self.auth_type,
                is_superuser=self.is_superuser
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
            fields_values=self.user.get_dynamic_mapping()
        )
        template_data['template_owners'] = list(
            UserModel.objects.on_account(
                self.account.id
            ).order_by('id').values_list('id', flat=True)
        )
        if not self.account.is_free:
            template_data['is_active'] = True
        elif self.account.active_templates < self.account.max_active_templates:
            template_data['is_active'] = True
        else:
            template_data['is_active'] = False

        for task_data in template_data['tasks']:
            if not task_data.get('api_name'):
                task_data['api_name'] = create_api_name(prefix='task')
            if not task_data.get('raw_performers'):
                task_data['raw_performers'] = [
                    {
                        'type': PerformerType.USER,
                        'source_id': self.user.id
                    }
                ]

        generic_name = template_data.pop('generic_name', None)
        template_type = sys_template_type_map[system_template.type]

        # TemplateSerializer does not support 'type' and 'generic_name' fields,
        # for this reason the fields are passed through the form context
        from pneumatic_backend.processes.api_v2.serializers \
            .template.template import TemplateSerializer

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
            }
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
        system_template: SystemTemplate
    ) -> Template:

        template = self.create_template_from_sys_template(
            system_template=system_template
        )
        AnalyticService.template_created_from_landing_library(
            user=self.user,
            template=template,
            auth_type=self.auth_type,
            is_superuser=self.is_superuser,
        )
        return template
