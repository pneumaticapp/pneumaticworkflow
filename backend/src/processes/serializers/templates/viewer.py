from typing import Any, Dict

from rest_framework.serializers import (
    CharField,
    ModelSerializer,
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
            viewer_data['user_id'] = validated_data['source_id']
        elif validated_data['type'] == ViewerType.GROUP:
            viewer_data['group_id'] = validated_data['source_id']
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
        return self.create_or_update_instance(
            instance=instance,
            validated_data={
                'template': self.context['template'],
                'account':  self.context.get('account'),
                **validated_data,
            },
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
