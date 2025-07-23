from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from pneumatic_backend.accounts.models import (
    UserInvite,
    UserGroup
)
from pneumatic_backend.accounts.enums import (
    SourceType,
    Language,
)
from pneumatic_backend.accounts.messages import MSG_A_0002, MSG_A_0040
from pneumatic_backend.generics.mixins.serializers import (
    CustomValidationErrorMixin
)


UserModel = get_user_model()


class UserListInviteSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserInvite
        fields = (
            'id',
            'invited_by',
            'date_created',
            'invited_from',
            'by_username',
        )

    by_username = serializers.SerializerMethodField()

    def get_by_username(self, instance):
        if instance.invited_by is not None:
            return instance.invited_by.name_by_status
        return None


class UserInviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserInvite
        fields = (
            'id',
            'email',
            'status',
            'date_created',
            'date_updated',
            'is_staff',
            'invited_by',
        )


class AcceptInviteSerializer(
    CustomValidationErrorMixin,
    serializers.ModelSerializer,
):

    class Meta:
        model = UserModel
        fields = (
            'first_name',
            'last_name',
            'password',
            'timezone',
            'language',
        )

    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128, min_length=6)
    language = serializers.ChoiceField(
        choices=Language.EURO_CHOICES,
        required=False,
    )


class InviteUserSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer
):

    email = serializers.EmailField(required=True)
    type = serializers.ChoiceField(
        choices=SourceType.CHOICES,
        required=False
    )
    groups = serializers.ListField(
        required=False,
        child=serializers.IntegerField()
    )
    invited_from = serializers.ChoiceField(
        choices=SourceType.CHOICES,
        required=False
    )
    first_name = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    last_name = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    photo = serializers.URLField(
        required=False,
        allow_blank=True,
        allow_null=True,
        source='avatar'
    )

    def validate_email(self, value):
        return value.lower()

    def validate_groups(self, value):
        groups = UserGroup.objects.filter(
            account=self.context['account_id'],
            id__in=value
        )
        if groups.count() != len(value):
            raise ValidationError(MSG_A_0040)
        return value

    def validate(self, data):
        data = super().validate(data)
        if data.get('invited_from', data.get('type')) is None:
            raise ValidationError(MSG_A_0002)
        if data.get('invited_from') is None:
            data['invited_from'] = data.pop('type')
        return data


class InviteUsersSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer
):

    users = InviteUserSerializer(many=True, required=True)


class TokenSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer
):
    token = serializers.CharField(
        required=True,
        allow_null=False,
        allow_blank=False
    )
