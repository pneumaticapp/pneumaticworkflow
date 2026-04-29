from django.contrib.auth import get_user_model
from rest_framework.serializers import (
    EmailField,
    IntegerField,
    ModelSerializer,
    Serializer,
    SerializerMethodField,
)

from src.generics.fields import TimeStampField
from src.generics.mixins.serializers import (
    CustomValidationErrorMixin,
)
from src.processes.models.workflows.task import TaskPerformer

UserModel = get_user_model()


class TaskPerformerSerializer(
    CustomValidationErrorMixin,
    Serializer,
):

    user_id = IntegerField(required=True)


class TaskUserGroupPerformerSerializer(
    CustomValidationErrorMixin,
    ModelSerializer,
):
    class Meta:
        model = TaskPerformer
        fields = (
            'is_completed',
            'date_completed_tsp',
            'type',
            'source_id',
        )

    source_id = SerializerMethodField()
    date_completed_tsp = TimeStampField(source='date_completed')

    def get_source_id(self, instance):
        return (
            instance.group_id if instance.type == 'group' else instance.user_id
        )


def get_performers_for_task(task) -> list:
    """Serialize active (non-deleted) performers for a given task.

    Shared by WorkflowCurrentTaskSerializer and TaskSerializer to
    avoid duplicating the serialization logic.

    Uses prefetched ``all_performers`` (set by the workflow list
    queryset via ``to_attr``) when available to avoid N+1 queries.
    """
    if hasattr(task, 'all_performers'):
        performers = task.all_performers
    else:
        performers = task.exclude_directly_deleted_taskperformer_set()
    return TaskUserGroupPerformerSerializer(performers, many=True).data


class TaskGuestPerformerSerializer(
    CustomValidationErrorMixin,
    Serializer,
):

    email = EmailField(required=True)

    def validate_email(self, value):
        return value.lower()


class TaskGroupPerformerSerializer(
    CustomValidationErrorMixin,
    Serializer,
):
    group_id = IntegerField(required=True)
