from typing import Any, Dict

from rest_framework.serializers import (
    ModelSerializer,
)

from src.generics.fields import AccountPrimaryKeyRelatedField
from src.generics.mixins.serializers import (
    AdditionalValidationMixin,
    CustomValidationErrorMixin,
)
from src.processes.models.templates.fieldset import FieldsetTemplate
from src.processes.models.templates.kickoff import Kickoff
from src.processes.serializers.templates.field import (
    FieldTemplateListSerializer,
    FieldTemplateSerializer,
    FieldTemplateShortViewSerializer,
)
from src.processes.serializers.templates.fieldset import (
    FieldsetTemplateSerializer,
)
from src.processes.serializers.templates.mixins import (
    CreateOrUpdateInstanceMixin,
    CreateOrUpdateRelatedMixin,
)


class KickoffSerializer(
    CreateOrUpdateInstanceMixin,
    CreateOrUpdateRelatedMixin,
    CustomValidationErrorMixin,
    AdditionalValidationMixin,
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
    fieldsets = AccountPrimaryKeyRelatedField(
        many=True,
        queryset=FieldsetTemplate.objects.all(),
        required=False,
        allow_empty=True,
        default=list,
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
        fieldsets = validated_data.pop('fieldsets', None) or []
        instance = self.create_or_update_instance(
            validated_data={
                'template': self.context['template'],
                'account':  self.context.get('account'),
                **validated_data,
            },
        )
        instance.fieldsets.set(fieldsets)
        self.create_or_update_related(
            data=validated_data.get('fields'),
            ancestors_data={
                'kickoff': instance,
                'template': self.context['template'],
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
        fieldsets = validated_data.pop('fieldsets', None) or []
        instance = self.create_or_update_instance(
            instance=instance,
            validated_data={
                'template': self.context['template'],
                'account':  self.context.get('account'),
                **validated_data,
            },
        )
        instance.fieldsets.set(fieldsets)
        self.create_or_update_related(
            data=validated_data.get('fields'),
            ancestors_data={
                'kickoff': instance.id,
                'template': self.context['template'],
            },
            slz_cls=FieldTemplateSerializer,
            slz_context={
                **self.context,
                'kickoff': instance,
            },
        )
        return instance


class KickoffOnlyFieldsSerializer(ModelSerializer):
    class Meta:
        model = Kickoff
        fields = (
            'fields',
            'fieldsets',
        )

    fields = FieldTemplateShortViewSerializer(
        many=True,
        required=False,
        read_only=True,
    )

    def to_representation(self, instance):
        # TODO Delete when the Template <-> Kickoff relation becomes o2o
        from django.db import models  # noqa : PLC0415
        if isinstance(instance, models.Manager):
            instance = instance.first()
        if instance is None:
            return {'fields': [], 'fieldsets': []}
        return super().to_representation(instance)


class KickoffListSerializer(ModelSerializer):

    class Meta:
        model = Kickoff
        fields = (
            'fields',
            'fieldsets',
        )

    fields = FieldTemplateListSerializer(many=True)
    fieldsets = FieldsetTemplateSerializer(many=True)
