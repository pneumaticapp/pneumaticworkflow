from typing import Any, Dict

from rest_framework.serializers import (
    ModelSerializer,
)
from src.generics.mixins.serializers import (
    AdditionalValidationMixin,
    CustomValidationErrorMixin,
)
from src.processes.models.templates.kickoff import Kickoff
from src.processes.serializers.templates.field import (
    FieldTemplateListSerializer,
    FieldTemplateSerializer,
)
from src.processes.serializers.templates.fieldset import (
    FieldsetTemplateSerializer,
)
from src.processes.serializers.templates.mixins import (
    CreateOrUpdateInstanceMixin,
    CreateOrUpdateRelatedMixin,
    FieldsetMixin,
)


class KickoffSerializer(
    CreateOrUpdateInstanceMixin,
    CreateOrUpdateRelatedMixin,
    CustomValidationErrorMixin,
    AdditionalValidationMixin,
    FieldsetMixin,
    ModelSerializer,
):

    class Meta:
        model = Kickoff
        fields = (
            'fields',
            'fieldsets',
        )
        create_or_update_fields = {
            'account',
            'template',
        }

    fields = FieldTemplateSerializer(many=True, required=False, default=list)
    fieldsets = FieldsetTemplateSerializer(
        many=True,
        required=False,
        allow_empty=True,
    )

    def to_representation(self, instance):
        # TODO Delete when the Template <-> Kickoff relation becomes o2o
        from django.db import models  # noqa : PLC0415
        if isinstance(instance, models.Manager):
            instance = instance.first()
        if instance is None:
            return {'fields': [], 'fieldsets': []}
        return super().to_representation(instance)

    def create(self, validated_data: Dict[str, Any]):
        self.additional_validate(validated_data)
        template = self.context['template']
        instance = self.create_or_update_instance(
            validated_data={
                'template': template,
                'account':  self.context.get('account'),
                **validated_data,
            },
        )
        fieldsets_data = validated_data.pop('fieldsets', None)
        if fieldsets_data is not None:
            self.create_or_update_fieldsets(
                fieldsets_data=fieldsets_data,
                template=template,
                kickoff=instance,
                user=self.context['user'],
            )
        self.create_or_update_related(
            data=validated_data.get('fields'),
            ancestors_data={
                'kickoff': instance,
                'template': template,
            },
            slz_cls=FieldTemplateSerializer,
            slz_context={
                **self.context,
                'kickoff': instance,
            },
        )
        return instance

    def update(
        self,
        instance: Kickoff,
        validated_data: Dict[str, Any],
    ):
        self.additional_validate(validated_data)
        template = self.context['template']
        instance = self.create_or_update_instance(
            instance=instance,
            validated_data={
                'template': template,
                'account':  self.context.get('account'),
                **validated_data,
            },
        )
        fieldsets_data = validated_data.pop('fieldsets', None)
        if fieldsets_data is not None:
            self.create_or_update_fieldsets(
                fieldsets_data=fieldsets_data,
                template=template,
                kickoff=instance,
                user=self.context['user'],
            )
        self.create_or_update_related(
            data=validated_data.get('fields'),
            ancestors_data={
                'kickoff': instance.id,
                'template': template,
            },
            slz_cls=FieldTemplateSerializer,
            slz_context={
                **self.context,
                'kickoff': instance,
            },
        )
        return instance


class KickoffListSerializer(ModelSerializer):

    class Meta:
        model = Kickoff
        fields = (
            'fields',
            'fieldsets',
        )

    fields = FieldTemplateListSerializer(many=True)
    fieldsets = FieldsetTemplateSerializer(many=True)

    def to_representation(self, instance):
        # TODO Delete when the Template <-> Kickoff relation becomes o2o
        from django.db import models  # noqa : PLC0415
        if isinstance(instance, models.Manager):
            instance = instance.first()
        return super().to_representation(instance)
