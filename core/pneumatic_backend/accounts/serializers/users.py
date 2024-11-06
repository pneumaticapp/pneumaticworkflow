from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from pneumatic_backend.generics.fields import AccountPrimaryKeyRelatedField
from pneumatic_backend.generics.mixins.serializers import (
    CustomValidationErrorMixin
)
from pneumatic_backend.accounts.messages import MSG_A_0004


UserModel = get_user_model()


class ReassignSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer
):

    """ Old user from another account can have invite in current account.
        Therefore he can be an template owner or a performer"""

    old_user = AccountPrimaryKeyRelatedField(
        queryset=UserModel.objects,
    )
    new_user = AccountPrimaryKeyRelatedField(
        queryset=UserModel.objects,
    )

    def validate(self, attrs):
        if attrs['old_user'] == attrs['new_user']:
            raise ValidationError(MSG_A_0004)
        return attrs


class AcceptTransferSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer
):
    user_id = serializers.IntegerField(required=True)
    token = serializers.CharField(required=True)
