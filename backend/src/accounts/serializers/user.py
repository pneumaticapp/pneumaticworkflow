from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Prefetch, Q
from rest_framework import serializers

from src.accounts.enums import (
    Language,
    SourceType,
    Timezone,
)
from src.accounts.models import Contact
from src.accounts.serializers.group import (
    GroupNameSerializer,
)
from src.accounts.messages import (
    MSG_A_0036,
    MSG_A_0046,
    MSG_A_0049,
    MSG_A_0050,
)
from src.accounts.serializers.user_invites import (
    UserListInviteSerializer,
)
from src.generics.fields import (
    CommaSeparatedListField,
    DateFormatField,
    RelatedListField,
    TimeStampField,
)
from src.generics.mixins.serializers import (
    CustomValidationErrorMixin,
)
from src.processes.enums import (
    OwnerType,
    PerformerType,
)
from src.processes.models.templates.owner import TemplateOwner
from src.processes.models.templates.raw_performer import RawPerformerTemplate
from src.processes.models.templates.task import TaskTemplate
from src.processes.models.templates.template import Template
from src.processes.serializers.templates.template import (
    TemplateUserPrivilegesSerializer,
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
            'groups',
            'password',
            'manager_id',
            'report_ids',
        )
        read_only_fields = (
            'id',
            'type',
            'invite',
            'status',
            'is_account_owner',
            'date_joined_tsp',
        )

    groups = RelatedListField(
        source='user_groups',
        child=serializers.IntegerField(),
        required=False,
    )
    date_joined_tsp = TimeStampField(source='date_joined', read_only=True)
    timezone = serializers.ChoiceField(
        choices=Timezone.CHOICES,
        required=False,
    )
    date_fmt = DateFormatField(required=False)
    invite = serializers.SerializerMethodField(allow_null=True, read_only=True)
    password = serializers.CharField(write_only=True, required=False)
    manager_id = serializers.IntegerField(
        read_only=True,
        allow_null=True,
    )
    report_ids = RelatedListField(
        source='subordinates',
        child=serializers.IntegerField(),
        read_only=True,
    )

    def get_invite(self, instance: UserModel):
        if instance.status_invited and instance.invite:
            return UserListInviteSerializer(instance.invite).data
        return None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if Language.ru == settings.LANGUAGE_CODE:
            self.fields['language'].choices = Language.CHOICES
        else:
            self.fields['language'].choices = Language.EURO_CHOICES

    def validate_is_admin(self, value):
        if value is True and not self.context['user'].is_admin:
            raise serializers.ValidationError(MSG_A_0046)
        return value

    def validate(self, attrs):
        if 'password' in attrs:
            attrs['raw_password'] = attrs.pop('password')
        if (
            self.instance
            and self.instance.is_account_owner
            and self.instance != self.context['user']
        ):
            raise serializers.ValidationError(MSG_A_0036)
        return attrs


class UserPrivilegesSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        model = UserModel
        fields = UserSerializer.Meta.fields + (  # noqa : RUF005
            'templates',
        )
        read_only_fields = (
            UserSerializer.Meta.read_only_fields + (  # noqa : RUF005
                'templates',
            )
        )

    groups = GroupNameSerializer(
        source='user_groups',
        many=True,
        read_only=True,
    )
    templates = serializers.SerializerMethodField()

    def get_templates(self, instance: UserModel):
        groups = instance.user_groups.values_list('id', flat=True)

        templates = (
            Template.objects.filter(
                Q(account=instance.account) &
                (
                    Q(owners__type=OwnerType.USER,
                      owners__user=instance.id) |
                    Q(owners__type=OwnerType.GROUP,
                      owners__group__in=groups) |
                    Q(tasks__raw_performers__type=PerformerType.USER,
                      tasks__raw_performers__user=instance.id) |
                    Q(tasks__raw_performers__type=PerformerType.GROUP,
                      tasks__raw_performers__group__in=groups)
                ),
            )
            .distinct()
            .only('id', 'name', 'is_active', 'is_public')
            .prefetch_related(
                Prefetch(
                    'owners',
                    queryset=TemplateOwner.objects.filter(
                        Q(type=OwnerType.USER, user=instance.id) |
                        Q(type=OwnerType.GROUP, group__in=groups),
                    ).select_related(
                        'user', 'group',
                    ),
                ),
                Prefetch(
                    'tasks',
                    queryset=TaskTemplate.objects.filter(
                        Q(raw_performers__type=PerformerType.USER,
                          raw_performers__user=instance.id) |
                        Q(raw_performers__type=PerformerType.GROUP,
                          raw_performers__group__in=groups),
                    ).distinct().only(
                        'number', 'api_name', 'name',
                    ).prefetch_related(
                        Prefetch(
                            'raw_performers',
                            queryset=RawPerformerTemplate.objects.filter(
                                Q(type=PerformerType.USER, user=instance.id) |
                                Q(type=PerformerType.GROUP, group__in=groups),
                            ).distinct().select_related('user', 'group'),
                        ),
                    ),
                ),
            )
        )
        return TemplateUserPrivilegesSerializer(templates, many=True).data


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
                ('-first_name', '-first_name'),
                ('first_name', 'first_name'),
                ('last_name', 'last_name'),
                ('-last_name', '-last_name'),
                ('source', 'source'),
                ('-source', '-source'),
            ),
        ),
    )
    search = serializers.CharField(
        required=False,
    )
    source = serializers.ChoiceField(
        required=False,
        choices=SourceType.CHOICES,
    )
    limit = serializers.IntegerField(required=False)
    offset = serializers.IntegerField(required=False)


class SetManagerSerializer(
    CustomValidationErrorMixin,
    serializers.ModelSerializer,
):
    class Meta:
        model = UserModel
        fields = ('manager_id',)

    manager_id = serializers.PrimaryKeyRelatedField(
        queryset=UserModel.objects.all(),
        required=True,
        allow_null=False,
        source='manager',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['manager_id'].queryset = UserModel.objects.on_account(
            self.context['account'].id,
        ).active()

    def validate_manager_id(self, value):
        if value.id == self.instance.id:
            raise serializers.ValidationError(MSG_A_0049)

        current_manager = value
        visited = set()
        while current_manager:
            if current_manager.id in visited:
                break
            if current_manager.id == self.instance.id:
                raise serializers.ValidationError(MSG_A_0050)
            visited.add(current_manager.id)
            current_manager = current_manager.manager

        return value


class SetReportsSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer,
):
    report_ids = serializers.PrimaryKeyRelatedField(
        queryset=UserModel.objects.all(),
        required=True,
        allow_null=False,
        many=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[
            'report_ids'
        ].child_relation.queryset = UserModel.objects.on_account(
            self.context['account'].id,
        ).active()

    def validate_report_ids(self, value):
        manager_ids = set()
        current_manager = self.instance
        while current_manager:
            if current_manager.id in manager_ids:
                break
            manager_ids.add(current_manager.id)
            current_manager = current_manager.manager

        for report in value:
            if report.id == self.instance.id:
                raise serializers.ValidationError(MSG_A_0049)
            if report.id in manager_ids:
                raise serializers.ValidationError(MSG_A_0050)

        return value


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


class UserWebsocketSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = (
            'id',
            'first_name',
            'last_name',
            'email',
            'photo',
            'is_admin',
            'is_account_owner',
            'manager_id',
            'report_ids',
        )

    report_ids = RelatedListField(
        source='subordinates',
        child=serializers.IntegerField(),
        read_only=True,
    )
