# pylint: disable=attribute-defined-outside-init
import re
from typing import Dict, Any, List, Optional, Set

from django.db import transaction
from pneumatic_backend.processes.consts import TEMPLATE_NAME_LENGTH
from rest_framework.serializers import (
    Serializer,
    ModelSerializer,
    BooleanField,
    IntegerField,
    DateTimeField,
    CharField,
    ReadOnlyField,
    ValidationError,
    ChoiceField,
    ListField,
)
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import (
    ValidationError as ValidationCoreError
)
from pneumatic_backend.accounts.services import AccountService
from pneumatic_backend.processes.models import (
    Kickoff,
    Template,
    TemplateDraft,
)
from pneumatic_backend.generics.mixins.serializers import (
    AdditionalValidationMixin,
    CustomValidationErrorMixin
)
from pneumatic_backend.processes.api_v2.serializers.template.mixins import (
    CreateOrUpdateInstanceMixin,
    CreateOrUpdateRelatedMixin,
)
from pneumatic_backend.processes.api_v2.serializers.template.task import (
    TaskTemplateSerializer,
    TemplateTaskOnlyFieldsSerializer,
)
from pneumatic_backend.processes.api_v2.serializers.template.kickoff import (
    KickoffSerializer,
    KickoffOnlyFieldsSerializer,
    KickoffListSerializer,
)
from pneumatic_backend.processes.api_v2.serializers.template.task import (
    ShortTaskSerializer
)
from pneumatic_backend.processes.utils.common import (
    string_abbreviation,
    is_tasks_ordering_correct
)
from pneumatic_backend.processes.services.versioning.schemas import (
    TemplateSchemaV1,
)
from pneumatic_backend.processes.services.versioning.versioning import (
    TemplateVersioningService,
)
from pneumatic_backend.processes.messages import template as messages
from pneumatic_backend.accounts.validators import PayWallValidator
from pneumatic_backend.generics.validators import NoSchemaURLValidator
from pneumatic_backend.processes.enums import (
    PerformerType,
    TemplateOrdering,
    WorkflowApiStatus,
)
from pneumatic_backend.generics.exceptions import BaseServiceException
from pneumatic_backend.processes.api_v2.services.templates import (
    TemplateIntegrationsService
)
from pneumatic_backend.generics.fields import (
    RelatedListField,
    TimeStampField,
)
from pneumatic_backend.processes.enums import TemplateType
from pneumatic_backend.processes.utils.common import (
    VAR_PATTERN
)

UserModel = get_user_model()


class TemplateSerializer(
    CustomValidationErrorMixin,
    AdditionalValidationMixin,
    CreateOrUpdateInstanceMixin,
    CreateOrUpdateRelatedMixin,
    ModelSerializer
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
            'template_owners',
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
            'tasks_count',
            'performers_count'
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
            'tasks_count',
            'performers_count',
            'account',
        }

    name = CharField(required=True, max_length=TEMPLATE_NAME_LENGTH)
    description = CharField(allow_blank=True, default='')
    updated_by = IntegerField(read_only=True, source='updated_by_id')
    date_updated = DateTimeField(read_only=True)
    template_owners = RelatedListField(
        child=IntegerField(),
        required=False,
    )
    kickoff = KickoffSerializer(required=False)
    tasks = TaskTemplateSerializer(many=True, required=False)
    performers_count = ReadOnlyField()
    tasks_count = ReadOnlyField()
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
                                'is_required': is_required
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
        except (TypeError, ValueError, AttributeError):
            pass  # Will be raised in performer serializer
        return performers_ids

    def _get_template_owners_ids(self, data: Dict[str, Any]) -> List[int]:

        """ Return correct account template owners ids for draft
            If template owners is empty or incorrect don't rise an exception,
            but set to as the template owner of the current request user """

        template_owners_ids = set()
        raw_template_owners_ids = data.get('template_owners', [])
        if isinstance(raw_template_owners_ids, list):
            for user_id in raw_template_owners_ids:
                try:
                    template_owners_ids.add(int(user_id))
                except (TypeError, ValueError):
                    pass
        if template_owners_ids:
            template_owners_ids = list(
                self.context['account'].users.filter(
                    id__in=template_owners_ids
                ).values_list('id', flat=True)
            )
        if not template_owners_ids:
            template_owners_ids = [self.context['user'].id]
        return template_owners_ids

    def create_or_update_instance(
        self,
        validated_data: Dict[str, Any],
        instance: Optional[Template] = None
    ) -> Template:

        user = self.context['user']
        validated_data['updated_by'] = user
        validated_data['account'] = user.account
        validated_data['generic_name'] = self.context.get('generic_name')
        validated_data['type'] = self.context.get('type', TemplateType.CUSTOM)
        validated_data['name'] = string_abbreviation(
            validated_data['name'],
            TEMPLATE_NAME_LENGTH
        )
        performers_ids = self._get_template_performers_ids(validated_data)
        validated_data['tasks_count'] = len(validated_data['tasks'])
        validated_data['performers_count'] = len(performers_ids)
        if instance:
            validated_data['version'] = instance.version + 1
        else:
            validated_data['version'] = 0

        try:
            instance = super().create_or_update_instance(
                validated_data=validated_data,
                instance=instance
            )
        except BaseServiceException as ex:
            self.raise_validation_error(message=ex.message)
        else:
            instance.template_owners.set(
                validated_data.get('template_owners')
            )
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

        sys_vars = {'template-name', 'date'}
        sys_vars_is_used = bool(api_names_in_name & sys_vars)
        api_names_in_name -= sys_vars
        available_fields = self._get_raw_fields_from_kickoff(data)
        available_api_names = set(f['api_name'] for f in available_fields)
        failed_api_names = api_names_in_name - available_api_names
        if failed_api_names:
            self.raise_validation_error(
                message=messages.MSG_PT_0008,
                name='wf_name_template'
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
                    name='wf_name_template'
                )

    def additional_validate_kickoff(self, value: Dict[str, Any], **kwargs):
        if value is None:
            self.raise_validation_error(
                message=messages.MSG_PT_0010,
                name='kickoff'
            )
        if self.instance:
            kickoff = self.instance.kickoff_instance
            if value.get('id'):
                # TODO need API test
                kickoff_not_exist = kickoff and kickoff.id != value['id']
                if kickoff_not_exist:
                    self.raise_validation_error(
                        message=messages.MSG_PT_0011,
                        name='kickoff'
                    )
            else:
                creating_second_kickoff = kickoff is not None
                if creating_second_kickoff:
                    self.raise_validation_error(
                        message=messages.MSG_PT_0012,
                        name='kickoff'
                    )

    def additional_validate_tasks(self, value: List[Dict[str, Any]], **kwargs):

        if not value:
            self.raise_validation_error(message=messages.MSG_PT_0013)

        numbers = [task.get('number', 0) for task in value]
        # TODO need API test
        if not is_tasks_ordering_correct(numbers):
            self.raise_validation_error(
                message=messages.MSG_PT_0014,
                name='tasks'
            )

    def additional_validate(self, data: Dict[str, Any], **kwargs):
        if data.get('is_active'):
            user = self.context['user']
            account = user.account
            payment_required = (
                PayWallValidator.is_active_templates_limit_reached(
                    account=account
                )
            )
            if payment_required:
                self.raise_validation_error(
                    message=messages.MSG_PT_0015(account.max_active_templates),
                )
        super().additional_validate(data)

    def additional_validate_template_owners(self, *args, **kwargs):

        if not self.new_template_owners_ids:
            self.raise_validation_error(
                message=messages.MSG_PT_0016,
                name='template_owners'
            )
        if (
            self.context['account'].is_free
            and not self.template_owners_all_users
        ):
            self.raise_validation_error(
                message=messages.MSG_PT_0017,
                name='template_owners'
            )
        if self.context['user'].id not in self.new_template_owners_ids:
            self.raise_validation_error(
                message=messages.MSG_PT_0018,
                name='template_owners'
            )

        if self.undefined_user_ids:
            self.raise_validation_error(
                message=messages.MSG_PT_0019,
                name='template_owners'
            )

    def additional_validate_public_success_url(
        self,
        value: Dict[str, Any],
        **kwargs
    ):

        if value:
            if self.context['account'].is_free:
                self.raise_validation_error(
                    message=messages.MSG_PT_0020,
                    name='public_success_url'
                )
            try:
                NoSchemaURLValidator()(value)
            except ValidationCoreError:
                self.raise_validation_error(
                    message=messages.MSG_PT_0021,
                    name='public_success_url'
                )

    def to_representation(self, data: Dict[str, Any]):

        data = super(TemplateSerializer, self).to_representation(data)
        if data.get('description') is None:
            data['description'] = ''
        if data.get('template_owners') is None:
            data['template_owners'] = []
        if data.get('tasks') is None:
            data['tasks'] = []

        # TemplateSerializer cannot return a single Kickoff object
        # because the Template related with Kickoff by foreign key
        # instead of one to one relation. Getting the object manually:
        kickoff_slz = KickoffSerializer(
            instance=self.instance.kickoff_instance
        )
        data['kickoff'] = kickoff_slz.data
        return data

    def get_response_data(self) -> Dict[str, Any]:
        if self.instance.is_active:
            return self.data
        else:
            return self.instance.get_draft()

    def _update_draft(self, data: Dict[str, Any]):

        draft, _ = TemplateDraft.objects.get_or_create(
            template=self.instance
        )
        draft.draft = data
        draft.save()

    def _get_normalized_kickoff_draft(
        self,
        data: Optional[dict],
        instance: Kickoff
    ) -> dict:
        if isinstance(data, dict):
            data['fields'] = data.get('fields', [])
            data['description'] = data.get('description', '')
            data['id'] = instance.id
        else:
            data = {'id': instance.id, 'fields': [], 'description': ''}
        return data

    def save_as_draft(self) -> Template:

        """ Create empty Template instance
            and save not validated data to TemplateDraft """

        with transaction.atomic():
            user = self.context['user']
            data = self.initial_data
            tasks = data.get('tasks', [])
            performers_ids = self._get_template_performers_ids(data)
            data['name'] = data.get('name', '')
            data['is_public'] = bool(data.get('is_public'))
            data['is_embedded'] = bool(data.get('is_embedded'))
            data['template_owners'] = self._get_template_owners_ids(data)
            if not self.instance:
                self.instance = Template.objects.create(
                    account=user.account,
                    name=data.get('name') or 'New template',
                    is_active=False
                )
                self.instance.template_owners.add(user)
                service = TemplateIntegrationsService(
                    account=user.account,
                    user=user
                )
                service.create_integrations_for_template(
                    template=self.instance
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
            data['tasks_count'] = len(tasks)
            data['performers_count'] = len(performers_ids)
            kickoff, __ = Kickoff.objects.get_or_create(
                template_id=self.instance.id,
                defaults={'account_id': self.instance.account_id}
            )
            data['kickoff'] = self._get_normalized_kickoff_draft(
                data=data.get('kickoff'),
                instance=kickoff
            )
            self._update_draft(data=data)
            account_service = AccountService(
                instance=self.context['account'],
                user=user
            )
            account_service.update_active_templates()
            return self.instance

    def _set_constances(self, data: Dict[str, Any]):
        template_owners_data = data.get('template_owners')
        if template_owners_data:
            self.new_template_owners_ids = set(template_owners_data)
        else:
            self.new_template_owners_ids = set()
        self.in_account_user_ids = set(
            self.context['account'].get_user_ids(
                include_invited=True,
            )
        )
        self.template_owners_all_users = (
            self.new_template_owners_ids == self.in_account_user_ids
        )
        self.undefined_user_ids = (
            self.new_template_owners_ids - self.in_account_user_ids
        )

    def create(self, validated_data: Dict[str, Any]) -> Template:

        self._set_constances(validated_data)
        self.additional_validate(validated_data)
        user = self.context['user']
        account = user.account
        instance = self.create_or_update_instance(
            validated_data=validated_data
        )

        self.create_or_update_related_one(
            slz_cls=KickoffSerializer,
            data=validated_data['kickoff'],
            ancestors_data={
                'account': account,
                'template': instance
            },
            slz_context={
                **self.context,
                'template': instance,
            }
        )
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
            }
        )

        if instance.is_active:
            version_service = TemplateVersioningService(
                schema=TemplateSchemaV1
            )
            version_service.save(template=instance)
        service = TemplateIntegrationsService(
            account=user.account,
            user=user
        )
        service.create_integrations_for_template(
            template=instance
        )
        return instance

    def update(
        self,
        instance: Template,
        validated_data: Dict[str, Any]
    ) -> Template:

        self._set_constances(validated_data)
        self.additional_validate(validated_data)
        user = self.context['user']
        account = user.account
        instance = self.create_or_update_instance(
            validated_data=validated_data,
            instance=instance
        )

        self.create_or_update_related(
            slz_cls=KickoffSerializer,
            data=[validated_data['kickoff']],
            ancestors_data={
                'account': account,
                'template': instance
            },
            slz_context={
                **self.context,
                'template': instance,
            }
        )
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
            }
        )

        if instance.is_active:
            version_service = TemplateVersioningService(
                schema=TemplateSchemaV1
            )
            version_service.save(template=instance)
        return instance

    def save(self, **kwargs):
        with transaction.atomic():
            instance = super().save(**kwargs)
            self._update_draft(data=self.data)
            account_service = AccountService(
                instance=self.context['account'],
                user=self.context['user']
            )
            account_service.update_active_templates()
            return instance

    def discard_changes(self):
        with transaction.atomic():
            self.instance.is_active = True
            self.instance.save(update_fields=['is_active'])
            self._update_draft(data=self.data)
            account_service = AccountService(
                instance=self.context['account'],
                user=self.context['user']
            )
            account_service.update_active_templates()

    def get_analytics_counters(self) -> dict:
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
    Serializer
):

    is_template_owner = BooleanField(
        required=False,
        default=None,
        allow_null=True
    )
    is_active = BooleanField(
        required=False,
        default=None,
        allow_null=True
    )
    is_public = BooleanField(
        required=False,
        default=None,
        allow_null=True
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
            'template_owners',
            'performers_count',
            'name',
            'is_active',
            'is_public',
            'is_embedded',
            'description',
            'kickoff',
        )

    template_owners = ListField(child=IntegerField())
    kickoff = KickoffListSerializer()


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
            instance=self.instance.kickoff_instance
        )
        data['kickoff'] = kickoff_slz.data
        return data

    def get_response_data(self) -> Dict[str, Any]:
        if self.instance.is_active:
            return self.data
        else:
            return self.instance.get_draft()


class TemplateTitlesRequestSerializer(
    CustomValidationErrorMixin,
    Serializer,
):

    with_tasks_in_progress = BooleanField(
        required=False,
        allow_null=True,
        default=None
    )
    workflows_status = ChoiceField(
        choices=WorkflowApiStatus.CHOICES,
        required=False,
        allow_null=False
    )

    def validate(self, attrs):
        if (
            attrs.get('workflows_status') is not None
            and attrs.get('with_tasks_in_progress') is not None
        ):
            raise ValidationError(messages.MSG_PT_0022)
        return attrs


class TemplateTitlesEventsRequestSerializer(
    CustomValidationErrorMixin,
    Serializer,
):

    event_date_from = DateTimeField(required=False, allow_null=False)
    event_date_to = DateTimeField(required=False, allow_null=False)


class TemplateAiSerializer(
    CustomValidationErrorMixin,
    Serializer
):

    description = CharField(
        required=True,
        allow_null=False,
        allow_blank=False,
        max_length=500
    )


class TemplateByStepsSerializer(
    CustomValidationErrorMixin,
    Serializer
):

    name = CharField(
        required=True,
        allow_null=False,
        allow_blank=False,
    )
    tasks = ShortTaskSerializer(
        many=True,
        required=True,
        allow_null=False
    )

    def validate_name(self, value):
        return value[:TEMPLATE_NAME_LENGTH]


class TemplateByNameSerializer(
    CustomValidationErrorMixin,
    Serializer
):

    name = CharField(
        required=True,
        allow_null=False,
        allow_blank=False,
    )
