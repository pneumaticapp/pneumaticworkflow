from typing import Any, Dict

from rest_framework import serializers
from rest_framework.serializers import (
    CharField,
    ModelSerializer,
    SerializerMethodField,
)

from src.generics.mixins.serializers import (
    AdditionalValidationMixin,
)
from src.processes.enums import ViewerType
from src.processes.models.templates.viewer import TemplateViewer
from src.processes.serializers.templates.mixins import (
    CreateOrUpdateInstanceMixin,
    CreateOrUpdateRelatedMixin,
)


class TemplateViewerSerializer(
    CreateOrUpdateInstanceMixin,
    CreateOrUpdateRelatedMixin,
    AdditionalValidationMixin,
    ModelSerializer,
):
    class Meta:
        model = TemplateViewer
        api_primary_field = 'api_name'
        fields = (
            'api_name',
            'type',
            'source_id',
            'user_details',
            'group_details',
        )
        create_or_update_fields = {
            'api_name',
            'type',
            'source_id',
            'account',
            'template',
            'user_id',
            'group_id',
        }

    api_name = CharField(required=False, max_length=200)
    source_id = CharField(allow_null=True)
    user_details = SerializerMethodField()
    group_details = SerializerMethodField()

    def get_user_details(self, obj):
        if obj.type == ViewerType.USER and obj.user:
            return {
                'id': obj.user.id,
                'email': obj.user.email,
                'first_name': obj.user.first_name,
                'last_name': obj.user.last_name,
            }
        return None

    def get_group_details(self, obj):
        if obj.type == ViewerType.GROUP and obj.group:
            return {
                'id': obj.group.id,
                'name': obj.group.name,
            }
        return None

    def create(self, validated_data: Dict[str, Any]):
        self.additional_validate(validated_data)
        viewer_data = {
            'template': self.context['template'],
            'account': self.context['account'],
            'type': validated_data['type'],
        }
        if validated_data.get('api_name'):
            viewer_data['api_name'] = validated_data['api_name']
        if validated_data['type'] == ViewerType.USER:
            viewer_data['user_id'] = int(validated_data['source_id'])
        elif validated_data['type'] == ViewerType.GROUP:
            viewer_data['group_id'] = int(validated_data['source_id'])
        msg = (
            "Viewer with this api_name already exists for template "
            f"{self.context['template'].name}"
        )
        return self.create_or_update_instance(
            validated_data=viewer_data,
            not_unique_exception_msg=msg,
        )

    def update(
        self,
        instance: TemplateViewer,
        validated_data: Dict[str, Any],
    ):
        self.additional_validate(validated_data)
        viewer_data = {
            'template': self.context['template'],
            'account': self.context.get('account'),
            'type': validated_data['type'],
            'api_name': validated_data.get('api_name') or instance.api_name,
        }
        if validated_data['type'] == ViewerType.USER:
            viewer_data['user_id'] = int(validated_data['source_id'])
            viewer_data['group_id'] = None
        elif validated_data['type'] == ViewerType.GROUP:
            viewer_data['group_id'] = int(validated_data['source_id'])
            viewer_data['user_id'] = None
        msg = (
            "Viewer with this api_name already exists for template "
            f"{self.context['template'].name}"
        )
        return self.create_or_update_instance(
            instance=instance,
            validated_data=viewer_data,
            not_unique_exception_msg=msg,
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if isinstance(instance, TemplateViewer):
            data['type'] = instance.type
            data['api_name'] = instance.api_name
            if instance.type == ViewerType.USER:
                data['source_id'] = str(instance.user_id)
            elif instance.type == ViewerType.GROUP:
                data['source_id'] = str(instance.group_id)
        return data


class TemplateViewerCreateSerializer(ModelSerializer):
    """Simplified serializer for creating viewers via API"""

    class Meta:
        model = TemplateViewer
        fields = ('type', 'user_id', 'group_id')

    def validate(self, data):
        viewer_type = data.get('type')
        user_id = data.get('user_id')
        group_id = data.get('group_id')

        if viewer_type == ViewerType.USER and not user_id:
            raise serializers.ValidationError(
                'user_id is required for user type',
            )

        if viewer_type == ViewerType.GROUP and not group_id:
            raise serializers.ValidationError(
                'group_id is required for group type',
            )

        if viewer_type == ViewerType.USER and group_id:
            raise serializers.ValidationError(
                'group_id should not be provided for user type',
            )

        if viewer_type == ViewerType.GROUP and user_id:
            raise serializers.ValidationError(
                'user_id should not be provided for group type',
            )

        return data


class TemplateViewerListSerializer(ModelSerializer):
    """Serializer for listing viewers"""

    user_details = SerializerMethodField()
    group_details = SerializerMethodField()

    class Meta:
        model = TemplateViewer
        fields = ('id', 'api_name', 'type', 'user_details', 'group_details')

    def get_user_details(self, obj):
        if obj.type == ViewerType.USER and obj.user:
            return {
                'id': obj.user.id,
                'email': obj.user.email,
                'first_name': obj.user.first_name,
                'last_name': obj.user.last_name,
            }
        return None

    def get_group_details(self, obj):
        if obj.type == ViewerType.GROUP and obj.group:
            return {
                'id': obj.group.id,
                'name': obj.group.name,
            }
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.type == ViewerType.USER and instance.user_id:
            data['source_id'] = str(instance.user_id)
        elif instance.type == ViewerType.GROUP and instance.group_id:
            data['source_id'] = str(instance.group_id)
        else:
            data['source_id'] = None
        return data
