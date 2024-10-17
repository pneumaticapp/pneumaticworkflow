from typing import Dict, Any
from rest_framework.serializers import (
    ModelSerializer,
    IntegerField,
    CharField
)
from pneumatic_backend.processes.models import (
    Kickoff
)
from pneumatic_backend.processes.api_v2.serializers.template.field import (
    FieldTemplateSerializer,
    FieldTemplateShortViewSerializer,
    FieldTemplateListSerializer
)
from pneumatic_backend.generics.mixins.serializers import (
    AdditionalValidationMixin,
    CustomValidationErrorMixin
)
from pneumatic_backend.processes.api_v2.serializers.template.mixins import (
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
        api_primary_field = 'id'
        fields = (
            'id',
            'description',
            'fields'
        )
        create_or_update_fields = {
            'account',
            'template',
            'description'
        }

    id = IntegerField(required=False)
    description = CharField(allow_blank=True, default='')
    fields = FieldTemplateSerializer(many=True, required=False)

    def to_representation(self, data: Dict[str, Any]):
        data = super(KickoffSerializer, self).to_representation(data)
        if data.get('description') is None:
            data['description'] = ''
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
            'id',
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
            'id',
            'description',
            'fields',
        )

    fields = FieldTemplateListSerializer(many=True)
