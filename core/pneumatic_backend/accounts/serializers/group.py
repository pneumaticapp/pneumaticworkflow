from rest_framework.serializers import (
    ModelSerializer,
    IntegerField,
    CharField,
    ValidationError,
)
from django.contrib.auth import get_user_model
from pneumatic_backend.generics.mixins.serializers import (
    CustomValidationErrorMixin
)
from pneumatic_backend.accounts.messages import MSG_A_0039
from pneumatic_backend.accounts.models import UserGroup
from pneumatic_backend.accounts.enums import (
    UserStatus,
)
from pneumatic_backend.generics.fields import RelatedListField
from rest_framework import serializers
from pneumatic_backend.generics.fields import CommaSeparatedListField

UserModel = get_user_model()


class GroupSerializer(
    CustomValidationErrorMixin,
    ModelSerializer
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
    users = RelatedListField(
        child=IntegerField(),
        required=False,
    )

    def validate_users(self, value):
        if value:
            users = UserModel.objects.filter(
                id__in=value,
                status__in=(UserStatus.ACTIVE, UserStatus.INVITED),
                account=self.context['account']
            )
            if users.count() != len(value):
                raise ValidationError(MSG_A_0039)
        return value


class GroupRequestSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer
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
            )
        )
    )
