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
