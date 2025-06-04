from django.contrib.auth import get_user_model
from rest_framework.serializers import (
    Serializer,
    IntegerField,
    EmailField,
    SerializerMethodField,
    ModelSerializer
)
from pneumatic_backend.generics.fields import TimeStampField
from pneumatic_backend.processes.models.workflows.task import TaskPerformer
from pneumatic_backend.generics.mixins.serializers import (
    CustomValidationErrorMixin
)

UserModel = get_user_model()


class TaskPerformerSerializer(
    CustomValidationErrorMixin,
    Serializer
):

    user_id = IntegerField(required=True)


class TaskUserGroupPerformerSerializer(
    CustomValidationErrorMixin,
    ModelSerializer
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
    Serializer
):

    email = EmailField(required=True)

    def validate_email(self, value):
        return value.lower()


class TaskGroupPerformerSerializer(
    CustomValidationErrorMixin,
    Serializer
):
    group_id = IntegerField(required=True)
