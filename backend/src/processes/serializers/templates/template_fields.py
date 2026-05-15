from typing import Any, Dict

from rest_framework.fields import CharField
from rest_framework.serializers import (
    ModelSerializer,
)
from src.processes.models.templates.fields import FieldTemplate
from src.processes.models.templates.fieldset import (
    FieldsetTemplateTaskTemplate,
    FieldsetTemplateKickoff,
)
from src.processes.models.templates.kickoff import Kickoff
from src.processes.models.templates.template import Template
from src.processes.models.templates.task import TaskTemplate


# All serializers for the GET /templates/id/fields API


class FieldTemplateOnlyFieldsSerializer(ModelSerializer):

    class Meta:
        model = FieldTemplate
        fields = (
            'name',
            'type',
            'order',
            'description',
            'is_hidden',
            'api_name',
        )


class FieldsetTemplateKickoffListSerializer(ModelSerializer):

    class Meta:
        model = FieldsetTemplateKickoff
        fields = (
            'order',
            'name',
            'description',
            'fields',
            'api_name',
            'label_position',
            'layout',
        )

    name = CharField(source='fieldset.name')
    description = CharField(source='fieldset.description')
    api_name = CharField(source='fieldset.api_name')
    label_position = CharField(
        source='fieldset.label_position',
    )
    layout = CharField(source='fieldset.layout')
    fields = FieldTemplateOnlyFieldsSerializer(
        source='fieldset.fields',
        many=True,
    )


class FieldsetTaskTemplateOnlyFieldsSerializer(ModelSerializer):

    class Meta:
        model = FieldsetTemplateTaskTemplate
        fields = (
            'order',
            'name',
            'description',
            'fields',
            'api_name',
            'label_position',
            'layout',
        )

    name = CharField(source='fieldset.name')
    description = CharField(source='fieldset.description')
    api_name = CharField(source='fieldset.api_name')
    label_position = CharField(
        source='fieldset.label_position',
    )
    layout = CharField(source='fieldset.layout')
    fields = FieldTemplateOnlyFieldsSerializer(
        source='fieldset.fields',
        many=True,
    )


class KickoffOnlyFieldsSerializer(ModelSerializer):

    class Meta:
        model = Kickoff
        fields = (
            'fields',
            'fieldsets',
        )

    fields = FieldTemplateOnlyFieldsSerializer(
        many=True,
        default=[],
        read_only=True,
    )
    fieldsets = FieldsetTemplateKickoffListSerializer(
        source='fieldsettemplatekickoff_set',
        many=True,
        default=[],
        read_only=True,
    )

    def to_representation(self, instance):
        # TODO Delete when the Template <-> Kickoff relation becomes o2o
        from django.db import models  # noqa : PLC0415
        if isinstance(instance, models.Manager):
            instance = instance.first()
        return super().to_representation(instance)


class TemplateTaskOnlyFieldsSerializer(ModelSerializer):

    class Meta:
        model = TaskTemplate
        fields = (
            'name',
            'number',
            'api_name',
            'fields',
            'fieldsets',
        )

    fields = FieldTemplateOnlyFieldsSerializer(
        many=True,
        default=[],
        read_only=True,
    )
    fieldsets = FieldsetTaskTemplateOnlyFieldsSerializer(
        source='fieldsettemplatetasktemplate_set',
        many=True,
        default=[],
        read_only=True,
    )


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
