from django.contrib.auth import get_user_model
from rest_framework import serializers

from src.accounts.models import UserGroup
from src.generics.fields import AccountPrimaryKeyRelatedField
from src.generics.mixins.serializers import (
    CustomValidationErrorMixin,
)

UserModel = get_user_model()


class ReassignSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer,
):

    """ Old user/group from can be reassigned to new user/group
        At least one pair (old_user/old_group) and (new_user/new_group)
        should be specified """

    old_user = AccountPrimaryKeyRelatedField(
        queryset=UserModel.objects,
        required=False,
        allow_null=True,
    )
    new_user = AccountPrimaryKeyRelatedField(
        queryset=UserModel.objects,
        required=False,
        allow_null=True,
    )
    old_group = AccountPrimaryKeyRelatedField(
        queryset=UserGroup.objects,
        required=False,
        allow_null=True,
    )
    new_group = AccountPrimaryKeyRelatedField(
        queryset=UserGroup.objects,
        required=False,
        allow_null=True,
    )


class AcceptTransferSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer,
):
    user_id = serializers.IntegerField(required=True)
    token = serializers.CharField(required=True)
