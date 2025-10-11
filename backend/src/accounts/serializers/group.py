# ruff: noqa: PLC0415
from rest_framework.serializers import (
    ModelSerializer,
    IntegerField,
    CharField,
    ValidationError,
)
from django.contrib.auth import get_user_model
from src.generics.mixins.serializers import (
    CustomValidationErrorMixin,
)
from src.accounts.messages import MSG_A_0039
from src.accounts.models import UserGroup
from src.accounts.enums import (
    UserStatus,
)
from src.generics.fields import RelatedListField
from rest_framework import serializers
from src.generics.fields import CommaSeparatedListField

UserModel = get_user_model()


class GroupSerializer(
    CustomValidationErrorMixin,
    ModelSerializer,
):
    class Meta:
        model = UserGroup
        fields = (
            'id',
            'name',
            'photo',
            'users',
        )

    id = IntegerField(read_only=True)
    name = CharField(max_length=255, required=True)
    photo = serializers.URLField(
        required=True,
        allow_blank=True,
        allow_null=True,
    )
    users = RelatedListField(
        child=IntegerField(),
        required=False,
    )

    def validate_photo(self, value):
        if value is None:
            return ""
        return value

    def validate_users(self, value):
        if value:
            users = UserModel.objects.filter(
                id__in=value,
                status__in=(UserStatus.ACTIVE, UserStatus.INVITED),
                account=self.context['account'],
            )
            if users.count() != len(value):
                raise ValidationError(MSG_A_0039)
        return value


class GroupRequestSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer,
):

    ordering = CommaSeparatedListField(
        allow_empty=True,
        allow_null=False,
        required=False,
        child=serializers.ChoiceField(
            allow_null=False,
            allow_blank=False,
            choices=(
                ('-name', '-name'),
                ('name', 'name'),
            ),
        ),
    )


class GroupNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserGroup
        fields = (
            'id',
            'name',
        )


class GroupWebsocketSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserGroup
        fields = (
            'id',
            'name',
            'photo',
            'users',
        )

    users = serializers.SerializerMethodField()

    def get_users(self, obj):
        from src.accounts.serializers.user import (
            UserWebsocketSerializer,
        )
        return UserWebsocketSerializer(obj.users.all(), many=True).data
