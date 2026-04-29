from typing import Any, Dict

from rest_framework.serializers import (
    IntegerField,
    ModelSerializer,
)

from src.generics.mixins.serializers import (
    AdditionalValidationMixin,
    CustomValidationErrorMixin,
)
from src.processes.models.hierarchy import (
    TaskTemplateHierarchyConfig,
)
from src.processes.serializers.templates.mixins import (
    CreateOrUpdateInstanceMixin,
)


class HierarchyConfigSerializer(
    CustomValidationErrorMixin,
    AdditionalValidationMixin,
    CreateOrUpdateInstanceMixin,
    ModelSerializer,
):

    """Nested serializer for TaskTemplateHierarchyConfig.

    Required slz context:
        task    - TaskTemplate instance (project convention)
        account - Account instance
    """

    class Meta:
        model = TaskTemplateHierarchyConfig
        fields = (
            'max_depth',
        )
        create_or_update_fields = {
            'task_template',
            'account',
            'max_depth',
        }

    max_depth = IntegerField(
        required=False,
        allow_null=True,
        min_value=1,
    )

    def create(self, validated_data: Dict[str, Any]):
        return self.create_or_update_instance(
            validated_data={
                'task_template': self.context['task'],
                'account': self.context['account'],
                **validated_data,
            },
        )

    def update(
        self,
        instance: TaskTemplateHierarchyConfig,
        validated_data: Dict[str, Any],
    ):
        return self.create_or_update_instance(
            instance=instance,
            validated_data={
                'task_template': self.context['task'],
                'account': self.context['account'],
                **validated_data,
            },
        )
