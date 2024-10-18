from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import serializers
from pneumatic_backend.accounts.models import Contact
from pneumatic_backend.accounts.serializers.user_invites import (
    UserListInviteSerializer
)
from pneumatic_backend.generics.fields import (
    TimeStampField,
    DateFormatField,
    RelatedListField,
)
from pneumatic_backend.accounts.enums import (
    SourceType,
    Language,
    Timezone
)
from pneumatic_backend.generics.fields import CommaSeparatedListField
from pneumatic_backend.generics.mixins.serializers import (
    CustomValidationErrorMixin
)


UserModel = get_user_model()


class UserSerializer(
    CustomValidationErrorMixin,
    serializers.ModelSerializer,
):

    class Meta:
        model = UserModel
        fields = (
            'id',
            'type',
            'email',
            'first_name',
            'last_name',
            'phone',
            'photo',
            'status',
            'is_admin',
            'is_staff',
            'date_joined',
            'date_joined_tsp',
            'is_account_owner',
            'is_tasks_digest_subscriber',
            'is_digest_subscriber',
            'is_newsletters_subscriber',
            'is_special_offers_subscriber',
            'is_new_tasks_subscriber',
            'is_complete_tasks_subscriber',
            'is_comments_mentions_subscriber',
            'language',
            'timezone',
            'date_fmt',
            'date_fdw',
            'invite',
            'groups'
        )
        read_only_fields = (
            'id',
            'type',
            'email',
            'invite',
            'status',
            'is_admin',
            'is_staff',
            'is_account_owner',
            'groups'
        )

    groups = RelatedListField(
        source='user_groups',
        child=serializers.IntegerField(),
        read_only=True
    )
    date_joined_tsp = TimeStampField(source='date_joined', read_only=True)
    timezone = serializers.ChoiceField(
        choices=Timezone.CHOICES,
        required=False
    )
    date_fmt = DateFormatField(required=False)
    invite = serializers.SerializerMethodField(allow_null=True, read_only=True)
    # TODO remove in https://my.pneumatic.app/workflows/34238/
    is_staff = serializers.BooleanField(source='is_admin', read_only=True)

    def get_invite(self, instance: UserModel):
        if instance.status_invited and instance.invite:
            return UserListInviteSerializer(instance.invite).data
        return None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if settings.LANGUAGE_CODE == Language.ru:
            self.fields['language'].choices = Language.CHOICES
        else:
            self.fields['language'].choices = Language.EURO_CHOICES


class UserNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = (
            'id',
            'first_name',
            'last_name',
        )


class ContactRequestSerializer(
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
                ('-first_name', '-first_name'),
                ('first_name', 'first_name'),
                ('last_name', 'last_name'),
                ('-last_name', '-last_name'),
                ('source', 'source'),
                ('-source', '-source'),
            )
        )
    )
    search = serializers.CharField(
        required=False,
    )
    source = serializers.ChoiceField(
        required=False,
        choices=SourceType.CHOICES
    )
    limit = serializers.IntegerField(required=False)
    offset = serializers.IntegerField(required=False)


class ContactResponseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Contact
        fields = (
            'id',
            'first_name',
            'last_name',
            'photo',
            'job_title',
            'source',
            'email',
        )
