from django.contrib.auth import get_user_model
from rest_framework.serializers import (
    Serializer,
    IntegerField,
    EmailField,
    CharField,
    SerializerMethodField
)
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
    Serializer
):
    type = CharField()
    source_id = SerializerMethodField()

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
