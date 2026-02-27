from django.contrib.auth import authenticate, get_user_model
from django.core.validators import RegexValidator
from drf_recaptcha.fields import ReCaptchaV2Field
from rest_framework import serializers
from typing import Any, Dict, Optional

from src.accounts.enums import Language
from src.accounts.models import Account
from src.authentication.messages import (
    MSG_AU_0006,
    MSG_AU_0012,
    MSG_AU_0013,
    MSG_AU_0020,
)
from src.generics.fields import DateFormatField, TimeStampField
from src.generics.mixins.services import EncryptionMixin
from src.generics.serializers import CustomValidationErrorMixin
from src.processes.models.templates.template import Template

UserModel = get_user_model()


class SignUpSerializer(
    CustomValidationErrorMixin,
    serializers.ModelSerializer,
):

    class Meta:
        model = UserModel
        fields = [
            'id',
            'email',
            'phone',
            'company_name',
            'first_name',
            'last_name',
            'photo',
            'timezone',
            'language',
            'password',
            'utm_source',
            'utm_medium',
            'utm_campaign',
            'utm_term',
            'utm_content',
            'gclid',
        ]

    email = serializers.EmailField(required=True)
    phone = serializers.CharField(
        required=False,
        allow_null=True,
        validators=[
            RegexValidator(regex=r'^\+?\d{9,16}$', message=MSG_AU_0006),
        ],
    )
    password = serializers.CharField(
        required=False,
        allow_null=True,
        min_length=6,
    )
    company_name = serializers.CharField(required=False)
    language = serializers.ChoiceField(
        choices=Language.EURO_CHOICES,
        required=False,
    )
    utm_source = serializers.CharField(required=False, allow_null=True)
    utm_medium = serializers.CharField(required=False, allow_null=True)
    utm_campaign = serializers.CharField(required=False, allow_null=True)
    utm_term = serializers.CharField(required=False, allow_null=True)
    utm_content = serializers.CharField(required=False, allow_null=True)
    gclid = serializers.CharField(required=False, allow_null=True)

    def validate_email(self, value: str):
        return value.lower()

    def validate_first_name(self, value: str):
        return value.title()

    def validate_last_name(self, value: str):
        return value.title()


class SecuredSignUpSerializer(SignUpSerializer):

    class Meta:
        model = UserModel
        fields = [
            'id',
            'email',
            'phone',
            'company_name',
            'first_name',
            'last_name',
            'photo',
            'timezone',
            'language',
            'password',
            'utm_source',
            'utm_medium',
            'utm_campaign',
            'utm_term',
            'utm_content',
            'gclid',
            'captcha',
        ]

    captcha = ReCaptchaV2Field()

    def validate(self, attrs):
        attrs = super().validate(attrs)
        attrs.pop('captcha', None)
        return attrs


class ContextAccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = Account
        fields = (
            'id',
            'name',
            'tenant_name',
            'date_joined',
            'date_joined_tsp',
            'is_blocked',  # deprecate
            'is_verified',
            'lease_level',
            'logo_lg',
            'logo_sm',
            'active_users',
            'tenants_active_users',
            'max_users',
            'is_subscribed',
            'billing_plan',
            'billing_sync',
            'billing_period',
            'plan_expiration',
            'plan_expiration_tsp',
            'trial_is_active',
            'trial_ended',
        )

    date_joined_tsp = TimeStampField(source='date_joined', read_only=True)
    plan_expiration_tsp = TimeStampField(
        source='plan_expiration',
        read_only=True,
    )
    is_blocked = serializers.SerializerMethodField()

    def get_is_blocked(self, instance):
        return False


class ContextUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserModel
        fields = (
            'id',
            'email',
            'account',
            'first_name',
            'last_name',
            'email',
            'phone',
            'photo',
            'is_admin',
            'date_joined',
            'date_joined_tsp',
            'is_account_owner',
            'is_superuser',
            'is_digest_subscriber',
            'is_newsletters_subscriber',
            'is_special_offers_subscriber',
            'is_new_tasks_subscriber',
            'is_complete_tasks_subscriber',
            'is_comments_mentions_subscriber',
            'is_tasks_digest_subscriber',
            'is_supermode',
            'type',
            'language',
            'timezone',
            'date_fmt',
            'date_fdw',
            'has_workflow_viewer_access',
            'has_workflow_starter_access',
        )

    account = ContextAccountSerializer()
    is_supermode = serializers.BooleanField(required=False)
    has_workflow_viewer_access = serializers.SerializerMethodField()
    has_workflow_starter_access = serializers.SerializerMethodField()
    date_joined_tsp = TimeStampField(source='date_joined', read_only=True)
    date_fmt = DateFormatField(read_only=True)

    def get_has_workflow_viewer_access(self, obj) -> bool:
        templates_qs = Template.objects.on_account(obj.account_id)
        return (
            templates_qs.with_template_viewer(obj.id).exists() or
            templates_qs.with_template_owner(obj.id).exists()
        )

    def get_has_workflow_starter_access(self, obj) -> bool:
        templates_qs = Template.objects.on_account(obj.account_id)
        return (
            templates_qs.with_template_starter(obj.id).exists() or
            templates_qs.with_template_viewer(obj.id).exists() or
            templates_qs.with_template_owner(obj.id).exists()
        )

    def to_representation(self, data):
        data = super().to_representation(data)
        data['is_supermode'] = self.context.get('is_supermode', False)
        return data


class BaseAuthSerializerMeta:
    fields = (
        'id',
        'email',
        'first_name',
        'last_name',
        'phone',
        'photo',
        'is_active',
    )
    read_only_fields = ('id', )
    extra_kwargs = {
        'email': {'validators': []},
    }


class UserResetPasswordSerializer(serializers.ModelSerializer):
    new_password = serializers.CharField()

    def update(self, instance, validated_data):
        password = validated_data.get('new_password')
        instance.set_password(password)
        instance.save(update_fields=['password'])
        return instance

    class Meta:
        model = UserModel
        fields = ('id', 'new_password')


class AuthTokenSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer,
):

    code = serializers.CharField(
        allow_null=False,
        allow_blank=False,
        required=True,
    )
    state = serializers.CharField(
        allow_null=False,
        allow_blank=False,
        required=True,
    )

    utm_source = serializers.CharField(required=False, allow_null=True)
    utm_medium = serializers.CharField(required=False, allow_null=True)
    utm_campaign = serializers.CharField(required=False, allow_null=True)
    utm_term = serializers.CharField(required=False, allow_null=True)
    utm_content = serializers.CharField(required=False, allow_null=True)
    gclid = serializers.CharField(required=False, allow_null=True)


class MSTokenSerializer(AuthTokenSerializer):

    session_state = serializers.CharField(
        allow_null=False,
        allow_blank=False,
        required=True,
    )
    client_info = serializers.CharField(
        allow_null=False,
        allow_blank=False,
        required=True,
    )


class SSOTokenSerializer(
    EncryptionMixin,
    CustomValidationErrorMixin,
    serializers.Serializer,
):
    code = serializers.CharField(
        allow_null=False,
        allow_blank=False,
        required=True,
    )
    state = serializers.CharField(
        allow_null=False,
        allow_blank=False,
        required=True,
    )

    def _extract_domain_from_state(self, state: str) -> Optional[str]:
        try:
            return self.decrypt(state[36:]) or None
        except ValueError:
            return None

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        attrs['domain'] = self._extract_domain_from_state(attrs['state'])
        return attrs


class GoogleTokenSerializer(AuthTokenSerializer):

    pass


class AuthUriSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer,
):
    domain = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
    )


class TokenSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer,
):
    token = serializers.CharField(
        required=True,
        allow_null=False,
        allow_blank=False,
    )


class ResetPasswordSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer,
):
    email = serializers.EmailField(required=True)


class ConfirmPasswordSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer,
):
    new_password = serializers.CharField()
    confirm_new_password = serializers.CharField()
    token = serializers.CharField(
        required=True,
        allow_null=False,
        allow_blank=False,
    )

    def validate(self, attrs):
        if attrs.get('new_password') != attrs.get('confirm_new_password'):
            raise serializers.ValidationError(MSG_AU_0013)
        return attrs


class ChangePasswordSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer,
):
    old_password = serializers.CharField()
    new_password = serializers.CharField()
    confirm_new_password = serializers.CharField()

    def validate(self, attrs):
        if attrs.get('new_password') != attrs.get('confirm_new_password'):
            raise serializers.ValidationError(MSG_AU_0013)
        return attrs

    def validate_old_password(self, value):
        user = authenticate(
            username=self.context['user'].email,
            password=value,
        )
        if not user:
            raise serializers.ValidationError(MSG_AU_0012)
        return value


class OktaLogoutSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer,
):
    """
    Simple JSON serializer for Okta logout requests.

    Only validates basic JSON structure, not specific field values.
    After bearer token validation, we trust Okta's data format.

    Supports two formats:
    1. iss_sub: {"sub_id": {"format": "iss_sub", "iss": "...", "sub": "..."}}
    2. email: {"sub_id": {"format": "email", "email": "user@domain.com"}}
    """

    # DictField automatically validates that sub_id is a dict
    sub_id = serializers.DictField(required=True)

    def validate(self, data):
        sub_id_data = data['sub_id']

        if 'format' not in sub_id_data:
            raise serializers.ValidationError(MSG_AU_0020)

        return {
            'format': sub_id_data['format'],
            'data': sub_id_data,
        }
