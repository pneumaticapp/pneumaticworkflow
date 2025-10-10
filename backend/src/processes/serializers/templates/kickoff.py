from typing import Dict, Any
from rest_framework.serializers import (
    ModelSerializer,
)
from src.processes.models import (
    Kickoff
)
from src.processes.serializers.templates.field import (
    FieldTemplateSerializer,
    FieldTemplateShortViewSerializer,
    FieldTemplateListSerializer
)
from src.generics.mixins.serializers import (
    AdditionalValidationMixin,
    CustomValidationErrorMixin
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
    ModelSerializer
):

    class Meta:
        model = Kickoff
        fields = (
            'fields',
        )
        create_or_update_fields = {
            'account',
            'template',
        }

    fields = FieldTemplateSerializer(many=True, required=False)

    def to_representation(self, data: Dict[str, Any]):
        data = super().to_representation(data)
        if data.get('fields') is None:
            data['fields'] = []
        return data

    def create(self, validated_data: Dict[str, Any]):
        self.additional_validate(validated_data)
        instance = self.create_or_update_instance(
            validated_data={
                'template': self.context['template'],
                'account':  self.context.get('account'),
                **validated_data
            }
        )
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
            }
        )
        return instance

    def update(
        self,
        instance: Kickoff,
        validated_data: Dict[str, Any]
    ):
        self.additional_validate(validated_data)
        instance = self.create_or_update_instance(
            instance=instance,
            validated_data={
                'template': self.context['template'],
                'account':  self.context.get('account'),
                **validated_data
            }
        )
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
            }
        )
        return instance


class KickoffOnlyFieldsSerializer(ModelSerializer):
    class Meta:
        model = Kickoff
        fields = (
            'fields',
        )

    fields = FieldTemplateShortViewSerializer(
        many=True,
        required=False,
        read_only=True,
    )


class KickoffListSerializer(ModelSerializer):

    class Meta:
        model = Kickoff
        fields = (
            'fields',
        )

    fields = FieldTemplateListSerializer(many=True)
