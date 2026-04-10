from typing import Any, Dict
from django.db.models import Q
from rest_framework import serializers

from src.generics.serializers import CustomValidationErrorMixin
from src.processes.models.templates.kickoff import Kickoff
from src.processes.models.workflows.fieldset import FieldSet
from src.processes.models.workflows.fields import TaskField
from src.processes.models.workflows.kickoff import KickoffValue
from src.processes.models.workflows.workflow import Workflow
from src.processes.serializers.workflows.field import (
    TaskFieldSerializer,
)
from src.processes.serializers.workflows.fieldset import (
    FieldSetSerializer,
)
from src.processes.services.exceptions import FieldsetServiceException
from src.processes.services.tasks.exceptions import (
    TaskFieldException,
)
from src.processes.services.tasks.task import (
    TaskFieldService,
)
from src.processes.services.workflows.fieldsets.fieldset import (
    FieldSetService,
)

from src.services.markdown import MarkdownService


class KickoffValueInfoSerializer(serializers.ModelSerializer):
    output = TaskFieldSerializer(many=True)
    fieldsets = FieldSetSerializer(many=True)

    class Meta:
        model = KickoffValue
        fields = (
            'id',
            'output',
            'fieldsets',
        )


class KickoffValueSerializer(
    CustomValidationErrorMixin,
    serializers.ModelSerializer,
):

    class Meta:
        model = KickoffValue
        fields = (
            'workflow',
            'kickoff',
            'account_id',
            'fields_data',
        )
    workflow = serializers.PrimaryKeyRelatedField(
        queryset=Workflow.objects.all(),
    )
    kickoff = serializers.PrimaryKeyRelatedField(
        queryset=Kickoff.objects.all(),
    )
    account_id = serializers.IntegerField()
    fields_data = serializers.DictField(
        write_only=True,
        allow_empty=True,
        required=False,
        allow_null=True,
    )

    def create(self, validated_data: Dict[str, Any]):
        fields_data = validated_data.pop('fields_data', {})
        kickoff = validated_data['kickoff']
        description = validated_data.get('description')
        if description:
            clear_description = MarkdownService.clear(description)
        else:
            clear_description = None
        instance = KickoffValue.objects.create(
            workflow=validated_data['workflow'],
            account_id=validated_data['account_id'],
            clear_description=clear_description,
        )
        workflow = validated_data['workflow']
        fieldset_templates = (
            kickoff.fieldsets
            .prefetch_related('rules', 'fields')
            .order_by('id')
        )
        try:
            for fieldset_template in fieldset_templates:
                service = FieldSetService(user=self.context['user'])
                service.create(
                    instance_template=fieldset_template,
                    account_id=workflow.account_id,
                    workflow=workflow,
                    kickoff=instance,
                    kickoff_id=instance.id,
                    fields_data=fields_data,
                )
                try:
                    service.validate_rules()
                except FieldsetServiceException as ex:
                    self.raise_validation_error(message=ex.message)
            for field_template in kickoff.fields.filter(fieldset__isnull=True):
                service = TaskFieldService(user=self.context['user'])
                service.create(
                    instance_template=field_template,
                    workflow_id=workflow.id,
                    kickoff_id=instance.id,
                    value=fields_data.get(field_template.api_name),
                )
        except (TaskFieldException, FieldsetServiceException) as ex:
            self.raise_validation_error(
                message=ex.message,
                api_name=getattr(ex, 'api_name', None),
            )
        return instance

    def update(
        self,
        instance: KickoffValue,
        validated_data: Dict[str, Any],
    ):
        fields_values: dict = validated_data.pop('fields_data', {})
        instance = super().update(instance, validated_data)
        if fields_values:
            fields = (
                TaskField.objects
                .filter(
                    Q(fieldset__kickoff=instance) | Q(kickoff=instance),
                    api_name__in=fields_values,
                )
            )
            fieldsets_ids = set()
            for field in fields:
                if field.fieldset_id:
                    fieldsets_ids.add(field.fieldset_id)
                service = TaskFieldService(
                    user=self.context['user'],
                    instance=field,
                )
                try:
                    service.partial_update(
                        value=fields_values[field.api_name],
                        force_save=True,
                    )
                except TaskFieldException as ex:
                    self.raise_validation_error(
                        message=ex.message,
                        api_name=field.api_name,
                    )
            if fieldsets_ids:
                fieldsets = FieldSet.objects.filter(id__in=fieldsets_ids)
                try:
                    for fieldset in fieldsets:
                        service = FieldSetService(
                            user=self.context['user'],
                            instance=fieldset,
                        )
                        service.validate_rules()
                except FieldsetServiceException as ex:
                    self.raise_validation_error(message=ex.message)
        return instance
