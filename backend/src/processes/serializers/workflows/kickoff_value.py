from typing import Any, Dict

from rest_framework import serializers

from src.generics.serializers import CustomValidationErrorMixin
from src.processes.models.templates.kickoff import Kickoff
from src.processes.models.workflows.kickoff import KickoffValue
from src.processes.models.workflows.workflow import Workflow
from src.processes.serializers.workflows.field import (
    TaskFieldSerializer,
)
from src.processes.services.tasks.exceptions import (
    TaskFieldException,
)
from src.processes.services.tasks.task import (
    TaskFieldService,
)
from src.services.markdown import MarkdownService


class KickoffValueInfoSerializer(serializers.ModelSerializer):
    output = TaskFieldSerializer(many=True)

    class Meta:
        model = KickoffValue
        fields = (
            'id',
            'output',
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
        for field_template in kickoff.fields.all():
            service = TaskFieldService(user=self.context['user'])
            try:
                service.create(
                    instance_template=field_template,
                    workflow_id=validated_data['workflow'].id,
                    kickoff_id=instance.id,
                    value=fields_data.get(field_template.api_name),
                )
            except TaskFieldException as ex:
                self.raise_validation_error(
                    message=ex.message,
                    api_name=field_template.api_name,
                )
        return instance

    def update(
        self,
        instance: KickoffValue,
        validated_data: Dict[str, Any],
    ):
        fields_data: dict = validated_data.pop('fields_data', {})
        instance = super().update(instance, validated_data)
        if fields_data:
            for task_field in self.instance.output.filter(
                api_name__in=fields_data.keys(),
            ):
                service = TaskFieldService(
                    user=self.context['user'],
                    instance=task_field,
                )
                try:
                    service.partial_update(
                        value=fields_data[task_field.api_name],
                        force_save=True,
                    )
                except TaskFieldException as ex:
                    self.raise_validation_error(
                        message=ex.message,
                        api_name=task_field.api_name,
                    )
        return instance
