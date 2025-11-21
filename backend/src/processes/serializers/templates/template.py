import re
from typing import Any, Dict, List, Optional, Set

from django.contrib.auth import get_user_model
from django.core.exceptions import (
    ValidationError as ValidationCoreError,
)
from django.db import transaction
from django.utils import timezone
from rest_framework.serializers import (
    BooleanField,
    CharField,
    ChoiceField,
    DateTimeField,
    IntegerField,
    ModelSerializer,
    Serializer,
    SerializerMethodField,
)

from src.generics.exceptions import BaseServiceException
from src.generics.fields import (
    TimeStampField,
)
from src.generics.mixins.serializers import (
    AdditionalValidationMixin,
    CustomValidationErrorMixin,
    ValidationUtilsMixin,
)
from src.generics.validators import NoSchemaURLValidator
from src.processes.consts import TEMPLATE_NAME_LENGTH
from src.processes.enums import (
    OwnerType,
    PerformerType,
    TemplateOrdering,
    TemplateType,
    WorkflowApiStatus, TaskStatus,
)
from src.processes.messages import template as messages
from src.processes.models.templates.kickoff import Kickoff
from src.processes.models.templates.owner import TemplateOwner
from src.processes.models.templates.template import (
    Template,
    TemplateDraft,
)
from src.processes.serializers.templates.kickoff import (
    KickoffListSerializer,
    KickoffOnlyFieldsSerializer,
    KickoffSerializer,
)
from src.processes.serializers.templates.mixins import (
    CreateOrUpdateInstanceMixin,
    CreateOrUpdateRelatedMixin,
)
from src.processes.serializers.templates.owner import (
    TemplateOwnerSerializer,
)
from src.processes.serializers.templates.task import (
    ShortTaskSerializer,
    TaskTemplatePrivilegesSerializer,
    TaskTemplateSerializer,
    TemplateTaskOnlyFieldsSerializer,
)
from src.processes.services.templates.integrations import (
    TemplateIntegrationsService,
)
from src.processes.services.versioning.schemas import (
    TemplateSchemaV1,
)
from src.processes.services.versioning.versioning import (
    TemplateVersioningService,
)
from src.processes.utils.common import (
    VAR_PATTERN,
    create_api_name,
    get_tasks_ancestors,
    get_tasks_parents,
    is_tasks_ordering_correct,
    string_abbreviation,
)

UserModel = get_user_model()


class TemplateSerializer(
    CustomValidationErrorMixin,
    AdditionalValidationMixin,
    CreateOrUpdateInstanceMixin,
    CreateOrUpdateRelatedMixin,
    ModelSerializer,
):
    """
        Requires the following context variables:
        user:         request.user
        account:      request.user.account
        is_superuser: request user is_superuser

        Not required:
        automatically_created - True for system created templates (onboarding)
    """

    class Meta:
        model = Template
        api_primary_field = 'id'
        fields = (
            'id',
            'name',
            'wf_name_template',
            'description',
            'tasks',
            'kickoff',
            'owners',
            'is_active',
            'is_public',
            'is_embedded',
            'public_url',
            'embed_url',
            'public_success_url',
            'finalizable',
            'updated_by',
            'date_updated',
            'date_updated_tsp',
        )
        create_or_update_fields = {
            'name',
            'wf_name_template',
            'description',
            'is_active',
            'is_public',
            'is_embedded',
            'public_success_url',
            'finalizable',
            'updated_by',
            'date_updated',
            'version',
            'type',
            'generic_name',
            'account',
        }

    name = CharField(required=True, max_length=TEMPLATE_NAME_LENGTH)
    description = CharField(allow_blank=True, default='')
    updated_by = IntegerField(read_only=True, source='updated_by_id')
    date_updated = DateTimeField(read_only=True)
    owners = TemplateOwnerSerializer(many=True, required=False)
    kickoff = KickoffSerializer(required=False)
    tasks = TaskTemplateSerializer(many=True, required=False)
    public_url = CharField(read_only=True)
    embed_url = CharField(read_only=True)
    public_success_url = CharField(allow_null=True, required=False)
    date_updated_tsp = TimeStampField(read_only=True, source='date_updated')

    def _get_raw_fields_from_kickoff(self, data: Dict[str, Any]) -> List[dict]:

        """ Return format:
            [
                {
                    'api_name': str,
                    'name': str,
                    'is_required': bool
                }
            ]
        """
        result = []
        try:
            fields = data['kickoff']['fields']
        except KeyError:
            pass
        else:
            try:
                for field in fields:
                    try:
                        api_name = field.get('api_name')
                        name = field.get('name')
                        is_required = field.get('is_required', False)
                        if api_name and name:
                            result.append({
                                'name': name,
                                'api_name': api_name,
                                'is_required': is_required,
                            })
                    except TypeError:
                        continue
            except TypeError:
                pass
        return result

    def _get_template_performers_ids(self, data: Dict[str, Any]) -> Set[int]:
        performers_ids = set()
        try:
            for task_data in data.get('tasks', []):
                for raw_performer in task_data.get('raw_performers') or ():
                    if raw_performer.get('type') == PerformerType.USER:
                        source_id = raw_performer.get('source_id')
                        if source_id:
                            performers_ids.add(int(source_id))
                            raw_performer['source_id'] = str(source_id)
                    if raw_performer.get('type') == PerformerType.GROUP:
                        pass
        except (TypeError, ValueError, AttributeError):
            pass  # Will be raised in performer serializer
        return performers_ids

    def _get_owners_for_draft(
        self, data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:

        """ Return correct account template owners ids for draft
            If template owners is empty or incorrect don't rise an exception,
            but set to as the template owner of the current request user """

        owners = data.get('owners') or []
        result = []
        try:
            for owner in owners:
                if (
                    isinstance(owner, dict)
                    and owner.get('source_id')
                    and owner.get('type') in (
                        OwnerType.USER,
                        OwnerType.GROUP,
                    )
                ):
                    owner['api_name'] = (
                        owner.get('api_name') or create_api_name(
                            prefix=TemplateOwner.api_name_prefix,
                        )
                    )
                    owner['source_id'] = str(owner['source_id'])
                    result.append(owner)

        except (TypeError, ValueError):
            result = [{
                'source_id': str(self.context['user'].id),
                'type': OwnerType.USER,
                'api_name': create_api_name(
                    prefix=TemplateOwner.api_name_prefix,
                ),
            }]
        if not result:
            result = [{
                'source_id': str(self.context['user'].id),
                'type': OwnerType.USER,
                'api_name': create_api_name(
                    prefix=TemplateOwner.api_name_prefix,
                ),
            }]
        return result

    def create_or_update_instance(
        self,
        validated_data: Dict[str, Any],
        instance: Optional[Template] = None,
    ) -> Template:

        user = self.context['user']
        validated_data['updated_by'] = user
        validated_data['account'] = user.account
        validated_data['generic_name'] = self.context.get('generic_name')
        validated_data['type'] = self.context.get('type', TemplateType.CUSTOM)
        validated_data['name'] = string_abbreviation(
            validated_data['name'],
            TEMPLATE_NAME_LENGTH,
        )
        performers_ids = self._get_template_performers_ids(validated_data)
        if instance:
            validated_data['version'] = instance.version + 1
        else:
            validated_data['version'] = 0

        try:
            instance = super().create_or_update_instance(
                validated_data=validated_data,
                instance=instance,
            )
        except BaseServiceException as ex:
            self.raise_validation_error(message=ex.message)
        else:
            instance.performers.set(performers_ids)
            return instance

    def additional_validate_wf_name_template(self, value: str, data: dict):

        """ Checks three cases:
            1. If api-name is in wf_name_template, this field is available
            (created in previous steps).
            2. If only api-names is in wf_name_template name, at least one
            field must be required. """

        if not value:
            return
        api_names_in_name = {
            api_name.strip()
            for api_name in VAR_PATTERN.findall(value)
        }
        if not api_names_in_name:
            return

        sys_vars = {'template-name', 'date', 'workflow-id'}
        sys_vars_is_used = bool(api_names_in_name & sys_vars)
        api_names_in_name -= sys_vars
        available_fields = self._get_raw_fields_from_kickoff(data)
        available_api_names = {f['api_name'] for f in available_fields}
        failed_api_names = api_names_in_name - available_api_names
        if failed_api_names:
            self.raise_validation_error(
                message=messages.MSG_PT_0008,
                name='wf_name_template',
            )

        contains_only_api_names = VAR_PATTERN.sub('', value).strip() == ''
        if contains_only_api_names and not sys_vars_is_used:
            not_required_fields = True
            for f in available_fields:
                if f['api_name'] in api_names_in_name and f['is_required']:
                    not_required_fields = False
                    break
            if not_required_fields:
                self.raise_validation_error(
                    message=messages.MSG_PT_0009,
                    name='wf_name_template',
                )

    def additional_validate_kickoff(self, value: Dict[str, Any], **kwargs):
        if value is None:
            self.raise_validation_error(
                message=messages.MSG_PT_0010,
                name='kickoff',
            )

    def additional_validate_tasks(self, value: List[Dict[str, Any]], **kwargs):

        if not value:
            self.raise_validation_error(message=messages.MSG_PT_0013)

        numbers = [task.get('number', 0) for task in value]
        # TODO need API test
        if not is_tasks_ordering_correct(numbers):
            self.raise_validation_error(
                message=messages.MSG_PT_0014,
                name='tasks',
            )
        # Validate tasks "revert task"
        revert_task_api_names = {}
        task_api_names = set()
        for task in value:
            revert_task_api_name = task.get('revert_task')
            task_api_names.add(task['api_name'])
            if revert_task_api_name:
                revert_task_api_names[revert_task_api_name] = task
        not_existent = revert_task_api_names.keys() - task_api_names
        if not_existent:
            revert_task_api_name = not_existent.pop()
            task = revert_task_api_names[revert_task_api_name]
            self.raise_validation_error(
                message=messages.MSG_PT_0059(
                    name=task['name'],
                    api_name=revert_task_api_name,
                ),
                api_name=task.get('api_name'),
            )

    def additional_validate_owners(self, *args, **kwargs):

        if not self.new_users_owners_ids and not self.new_groups_owners_ids:
            self.raise_validation_error(
                message=messages.MSG_PT_0016,
                name='owners',
            )

        count_new_owners_ids = (
            len(self.new_users_owners_ids) + len(self.new_groups_owners_ids)
        )
        if len(self.owners_data) != count_new_owners_ids:
            self.raise_validation_error(
                message=messages.MSG_PT_0057,
                name='owners',
            )
        all_users = self.new_users_owners_ids | self.users_in_groups_owners_ids
        if self.context['user'].id not in all_users:
            self.raise_validation_error(
                message=messages.MSG_PT_0018,
                name='owners',
            )

        if self.undefined_users_ids or self.undefined_groups_ids:
            self.raise_validation_error(
                message=messages.MSG_PT_0019,
                name='owners',
            )

    def additional_validate_public_success_url(
        self,
        value: Dict[str, Any],
        **kwargs,
    ):

        if value:
            try:
                NoSchemaURLValidator()(value)
            except ValidationCoreError:
                self.raise_validation_error(
                    message=messages.MSG_PT_0021,
                    name='public_success_url',
                )

    def to_representation(self, instance: Template):
        data = super().to_representation(instance)
        if data.get('description') is None:
            data['description'] = ''
        if data.get('tasks') is None:
            data['tasks'] = []
        # TemplateSerializer cannot return a single Kickoff object
        # because the Template related with Kickoff by foreign key
        # instead of one to one relation. Getting the object manually:
        kickoff_slz = KickoffSerializer(instance=instance.kickoff_instance)
        data['kickoff'] = kickoff_slz.data
        return data

    def get_response_data(self) -> Dict[str, Any]:
        if self.instance.is_active:
            return self.data
        return self.instance.get_draft()

    def _update_draft(self, data: Dict[str, Any]):

        draft, _ = TemplateDraft.objects.get_or_create(
            template=self.instance,
        )
        draft.draft = data
        draft.save()

    def _get_normalized_kickoff_draft(
        self,
        data: Optional[dict],
    ) -> dict:
        if isinstance(data, dict):
            data['fields'] = data.get('fields', [])
        else:
            data = {'fields': []}
        return data

    def save_as_draft(self) -> Template:

        """ Create empty Template instance
            and save not validated data to TemplateDraft """

        with transaction.atomic():
            user = self.context['user']
            data = self.initial_data
            data['name'] = data.get('name', '')
            data['is_public'] = bool(data.get('is_public'))
            data['is_embedded'] = bool(data.get('is_embedded'))
            data['owners'] = self._get_owners_for_draft(data)
            data['tasks'] = data.get('tasks') or []
            parents_by_tasks = get_tasks_parents(data['tasks'])
            ancestors_by_tasks = get_tasks_ancestors(parents_by_tasks)
            for task in data['tasks']:
                if task.get('api_name'):
                    task['parents'] = parents_by_tasks[task['api_name']]
                    task['ancestors'] = list(
                        ancestors_by_tasks[task['api_name']],
                    )
                else:
                    task['parents'] = []
                    task['ancestors'] = []
            if not self.instance:
                self.instance = Template.objects.create(
                    account=user.account,
                    name=data.get('name') or 'New template',
                    is_active=False,
                )
                TemplateOwner.objects.get_or_create(
                    type=OwnerType.USER,
                    user_id=user.id,
                    account=self.context['user'].account,
                    template=self.instance,
                )
                service = TemplateIntegrationsService(
                    account=user.account,
                    user=user,
                )
                service.create_integrations_for_template(
                    template=self.instance,
                )
            else:
                self.instance.is_active = False
                self.instance.save(update_fields=['is_active'])

            data['is_active'] = False
            data['public_url'] = self.instance.public_url
            data['embed_url'] = self.instance.embed_url
            date_now = timezone.now()
            data['date_updated'] = date_now.isoformat()
            data['date_updated_tsp'] = date_now.timestamp()
            data['updated_by'] = user.id
            data['id'] = self.instance.id
            Kickoff.objects.get_or_create(
                template_id=self.instance.id,
                defaults={'account_id': self.instance.account_id},
            )
            data['kickoff'] = self._get_normalized_kickoff_draft(
                data=data.get('kickoff'),
            )
            self._update_draft(data=data)
            return self.instance

    def _set_constances(self, data: Dict[str, Any]):
        self.owners_data = data.get('owners', [])
        self.new_users_owners_ids = {
            int(owner.get('source_id'))
            for owner in self.owners_data
            if owner.get('type') == OwnerType.USER
            and owner.get('source_id') is not None
        }
        self.new_groups_owners_ids = {
            int(owner.get('source_id'))
            for owner in self.owners_data
            if owner.get('type') == OwnerType.GROUP
            and owner.get('source_id') is not None
        }
        self.users_in_groups_owners_ids = (
            UserModel.objects
            .get_users_in_groups(group_ids=self.new_groups_owners_ids)
            .user_ids_set()
        )
        self.in_account_user_ids = set(
            self.context['account'].get_user_ids(include_invited=True),
        )
        self.in_account_group_ids = set(
            self.context['account'].get_group_ids(),
        )
        self.undefined_users_ids = (
            self.new_users_owners_ids - self.in_account_user_ids
        )
        self.undefined_groups_ids = (
            self.new_groups_owners_ids - self.in_account_group_ids
        )

    def create(self, validated_data: Dict[str, Any]) -> Template:

        self._set_constances(validated_data)
        self.additional_validate(validated_data)
        user = self.context['user']
        account = user.account
        instance = self.create_or_update_instance(
            validated_data=validated_data,
        )
        self.create_or_update_related(
            slz_cls=TemplateOwnerSerializer,
            data=validated_data['owners'],
            ancestors_data={
                'account': account,
                'template': instance,
            },
            slz_context={
                **self.context,
                'template': instance,
            },
        )
        self.create_or_update_related_one(
            slz_cls=KickoffSerializer,
            data=validated_data['kickoff'],
            ancestors_data={
                'account': account,
                'template': instance,
            },
            slz_context={
                **self.context,
                'template': instance,
            },
        )
        parents_by_tasks = get_tasks_parents(validated_data['tasks'])
        tasks_api_names = set(parents_by_tasks.keys())
        ancestors_by_tasks = get_tasks_ancestors(parents_by_tasks)
        self.create_or_update_related(
            data=validated_data['tasks'],
            ancestors_data={
                'template': instance,
                'account': account,
            },
            slz_cls=TaskTemplateSerializer,
            slz_context={
                **self.context,
                'template': instance,
                'tasks_api_names': tasks_api_names,
                'parents_by_tasks': parents_by_tasks,
                'ancestors_by_tasks': ancestors_by_tasks,
            },
        )

        if instance.is_active:
            version_service = TemplateVersioningService(
                schema=TemplateSchemaV1,
            )
            version_service.save(template=instance)
        service = TemplateIntegrationsService(
            account=user.account,
            user=user,
        )
        service.create_integrations_for_template(
            template=instance,
        )
        return instance

    def update(
        self,
        instance: Template,
        validated_data: Dict[str, Any],
    ) -> Template:

        self._set_constances(validated_data)
        self.additional_validate(validated_data)
        user = self.context['user']
        account = user.account
        instance = self.create_or_update_instance(
            validated_data=validated_data,
            instance=instance,
        )
        self.create_or_update_related(
            slz_cls=TemplateOwnerSerializer,
            data=validated_data['owners'],
            ancestors_data={
                'account': account,
                'template': instance,
            },
            slz_context={
                **self.context,
                'template': instance,
            },
        )
        self.create_or_update_related_one(
            slz_cls=KickoffSerializer,
            data=validated_data['kickoff'],
            ancestors_data={
                'account': account,
                'template': instance,
            },
            slz_context={
                **self.context,
                'template': instance,
            },
        )
        parents_by_tasks = get_tasks_parents(validated_data['tasks'])
        tasks_api_names = set(parents_by_tasks.keys())
        ancestors_by_tasks = get_tasks_ancestors(parents_by_tasks)
        self.create_or_update_related(
            data=validated_data['tasks'],
            ancestors_data={
                'template': instance,
                'account': account,
            },
            slz_cls=TaskTemplateSerializer,
            slz_context={
                **self.context,
                'template': instance,
                'tasks_api_names': tasks_api_names,
                'parents_by_tasks': parents_by_tasks,
                'ancestors_by_tasks': ancestors_by_tasks,
            },
        )

        if instance.is_active:
            version_service = TemplateVersioningService(
                schema=TemplateSchemaV1,
            )
            version_service.save(template=instance)
        return instance

    def save(self, **kwargs):
        with transaction.atomic():
            instance = super().save(**kwargs)
            self._update_draft(data=self.data)
            return instance

    def discard_changes(self):
        with transaction.atomic():
            self.instance.is_active = True
            self.instance.save(update_fields=['is_active'])
            self._update_draft(data=self.data)

    def get_analysis_counters(self) -> dict:
        data = self.initial_data
        tasks = data.get('tasks', [])
        tasks_fields_count = sum([
            len(task.get('fields', []))
            for task in tasks
        ])
        delays_count = len([task for task in tasks if task.get('delay')])
        due_date_count = len([
            task for task in tasks if task.get('raw_due_date')
        ])
        conditions_count = sum([
            len(task.get('conditions', []))
            for task in tasks if task.get('conditions', [])
        ])
        kickoff = data.get('kickoff', {})
        return {
            'kickoff_fields_count': len(kickoff.get('fields', [])),
            'tasks_count': len(tasks),
            'tasks_fields_count': tasks_fields_count,
            'delays_count': delays_count,
            'due_in_count': due_date_count,
            'conditions_count': conditions_count,
        }


class TemplateListFilterSerializer(
    CustomValidationErrorMixin,
    AdditionalValidationMixin,
    Serializer,
):

    is_active = BooleanField(
        required=False,
        default=None,
        allow_null=True,
    )
    is_public = BooleanField(
        required=False,
        default=None,
        allow_null=True,
    )
    search = CharField(required=False)
    ordering = ChoiceField(required=False, choices=TemplateOrdering.CHOICES)
    limit = IntegerField(min_value=0, required=False)
    offset = IntegerField(min_value=0, required=False)

    def validate_search(self, value: str) -> str:
        removed_chars_regex = r'\s\s+'
        clear_text = re.sub(removed_chars_regex, '', value).strip()
        return clear_text if clear_text else None


class TemplateListSerializer(ModelSerializer):

    class Meta:
        model = Template
        fields = (
            'id',
            'wf_name_template',
            'tasks_count',
            'workflows_count',
            'owners',
            'name',
            'is_active',
            'is_public',
            'is_embedded',
            'description',
            'kickoff',
        )

    owners = SerializerMethodField()
    kickoff = SerializerMethodField()
    tasks_count = IntegerField(read_only=True)
    workflows_count = IntegerField(read_only=True)

    def get_owners(self, instance: Template):
        return TemplateOwnerSerializer(instance.owners, many=True).data

    def get_kickoff(self, instance: Template):
        return KickoffListSerializer(instance.kickoff, many=True).data[0]


class TemplateOnlyFieldsSerializer(ModelSerializer):
    class Meta:
        model = Template
        fields = (
            'id',
            'kickoff',
            'tasks',
        )

    kickoff = KickoffOnlyFieldsSerializer(required=False, read_only=True)
    tasks = TemplateTaskOnlyFieldsSerializer(
        many=True,
        required=False,
        read_only=True,
    )

    def to_representation(self, data: Dict[str, Any]):

        data = super().to_representation(data)
        if data.get('tasks') is None:
            data['tasks'] = []

        # TemplateSerializer cannot return a single Kickoff object
        # because the Template related with Kickoff by foreign key
        # instead of one to one relation. Getting the object manually:
        kickoff_slz = KickoffOnlyFieldsSerializer(
            instance=self.instance.kickoff_instance,
        )
        data['kickoff'] = kickoff_slz.data
        return data

    def get_response_data(self) -> Dict[str, Any]:
        if self.instance.is_active:
            return self.data
        return self.instance.get_draft()


class TemplateTitlesByWorkflowsSerializer(
    CustomValidationErrorMixin,
    Serializer,
):

    status = ChoiceField(
        choices=WorkflowApiStatus.CHOICES,
        required=False,
        allow_null=False,
    )


class TemplateTitlesByTasksSerializer(
    CustomValidationErrorMixin,
    Serializer,
):

    status = ChoiceField(
        choices=TaskStatus.CHOICES,
        required=False,
        allow_null=False,
    )


class TemplateTitlesByEventsSerializer(
    CustomValidationErrorMixin,
    Serializer,
):

    date_from_tsp = TimeStampField(required=False, allow_null=True)
    date_to_tsp = TimeStampField(required=False, allow_null=True)


class TemplateAiSerializer(
    CustomValidationErrorMixin,
    Serializer,
):

    description = CharField(
        required=True,
        allow_null=False,
        allow_blank=False,
        max_length=500,
    )


class TemplateByStepsSerializer(
    CustomValidationErrorMixin,
    Serializer,
):

    name = CharField(
        required=True,
        allow_null=False,
        allow_blank=False,
    )
    tasks = ShortTaskSerializer(
        many=True,
        required=True,
        allow_null=False,
    )

    def validate_name(self, value):
        return value[:TEMPLATE_NAME_LENGTH]


class TemplateByNameSerializer(
    CustomValidationErrorMixin,
    Serializer,
):

    name = CharField(
        required=True,
        allow_null=False,
        allow_blank=False,
    )


class TemplateExportFilterSerializer(
    CustomValidationErrorMixin,
    ValidationUtilsMixin,
    Serializer,
):
    owners_ids = CharField(required=False)
    owners_group_ids = CharField(required=False)
    is_active = BooleanField(
        required=False,
        default=None,
        allow_null=True,
    )
    is_public = BooleanField(
        required=False,
        default=None,
        allow_null=True,
    )
    ordering = ChoiceField(
        required=False,
        choices=TemplateOrdering.CHOICES_EXPORT,
    )
    limit = IntegerField(min_value=0, required=False)
    offset = IntegerField(min_value=0, required=False)

    def validate_owners_ids(self, value):
        return self.get_valid_list_integers(value)

    def validate_owners_group_ids(self, value):
        return self.get_valid_list_integers(value)


class TemplateUserPrivilegesSerializer(
    CustomValidationErrorMixin,
    ModelSerializer,
):
    class Meta:
        model = Template
        fields = (
            'id',
            'name',
            'is_active',
            'is_public',
            'owners',
            'tasks',
        )

    owners = TemplateOwnerSerializer(many=True)
    tasks = TaskTemplatePrivilegesSerializer(many=True)


class TemplateDetailsSerializer(ModelSerializer):

    class Meta:
        model = Template
        fields = (
            'id',
            'name',
            'is_active',
            'wf_name_template',
        )


class WorkflowTemplateSerializer(ModelSerializer):

    class Meta:
        model = Template
        fields = (
            'id',
            'name',
            'is_active',
        )


class TemplateTitlesSerializer(Serializer):

    id = IntegerField(read_only=True)
    name = CharField(read_only=True)
    count = IntegerField(read_only=True)
