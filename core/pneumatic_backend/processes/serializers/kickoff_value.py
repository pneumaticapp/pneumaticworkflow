from typing import Any, Dict
from rest_framework import serializers
from pneumatic_backend.processes.models import KickoffValue
from pneumatic_backend.processes.serializers.task_field import (
    TaskFieldListSerializer,
)
from pneumatic_backend.processes.models import (
    Workflow,
    Kickoff,
)
from pneumatic_backend.generics.serializers import CustomValidationErrorMixin
from pneumatic_backend.processes.api_v2.services.task.field import (
    TaskFieldService
)
from pneumatic_backend.processes.api_v2.services.task.exceptions import (
    TaskFieldException
)
from pneumatic_backend.services.markdown import MarkdownService


class KickoffValueInfoSerializer(serializers.ModelSerializer):
    output = TaskFieldListSerializer(many=True)

    class Meta:
        model = KickoffValue
        fields = (
            'id',
            'description',
            'output',
        )


class KickoffValueSerializer(
    CustomValidationErrorMixin,
    serializers.ModelSerializer
):

    class Meta:
        model = KickoffValue
        fields = (
            'workflow',
            'kickoff',
            'description',
            'account_id',
            'fields_data'
        )
    workflow = serializers.PrimaryKeyRelatedField(
        queryset=Workflow.objects.all()
    )
    kickoff = serializers.PrimaryKeyRelatedField(
        queryset=Kickoff.objects.all()
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
            template_id=kickoff.id,
            account_id=validated_data['account_id'],
            description=description,
            clear_description=clear_description
        )
        for field_template in kickoff.fields.all():
            service = TaskFieldService(user=self.context['user'])
            try:
                service.create(
                    instance_template=field_template,
                    workflow_id=validated_data['workflow'].id,
                    kickoff_id=instance.id,
                    value=fields_data.get(field_template.api_name)
                )
            except TaskFieldException as ex:
                self.raise_validation_error(
                    message=ex.message,
                    api_name=field_template.api_name
                )
        return instance

    def update(
        self,
        instance: KickoffValue,
        validated_data: Dict[str, Any]
    ):
        fields_data: dict = validated_data.pop('fields_data', {})
        instance = super().update(instance, validated_data)
        if fields_data:
            for task_field in self.instance.output.filter(
                api_name__in=fields_data.keys()
            ):
                service = TaskFieldService(
                    user=self.context['user'],
                    instance=task_field
                )
                try:
                    service.partial_update(
                        value=fields_data[task_field.api_name],
                        force_save=True
                    )
                except TaskFieldException as ex:
                    self.raise_validation_error(
                        message=ex.message,
                        api_name=task_field.api_name
                    )
        return instance
