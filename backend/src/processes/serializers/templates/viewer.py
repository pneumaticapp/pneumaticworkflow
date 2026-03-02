from typing import Any, Dict

from rest_framework.serializers import (
    CharField,
    ModelSerializer,
    SerializerMethodField,
)

from src.generics.mixins.serializers import (
    AdditionalValidationMixin,
)
from src.processes.enums import ViewerType
from src.processes.messages.template import MSG_PT_0070
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
        return self.create_or_update_instance(
            validated_data=viewer_data,
            not_unique_exception_msg=MSG_PT_0070(
                name=self.context['template'].name,
                api_name=validated_data.get('api_name'),
            ),
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
        return self.create_or_update_instance(
            instance=instance,
            validated_data=viewer_data,
            not_unique_exception_msg=MSG_PT_0070(
                name=self.context['template'].name,
                api_name=validated_data.get('api_name'),
            ),
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
