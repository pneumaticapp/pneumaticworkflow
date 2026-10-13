from typing import Any, Dict, Optional

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.core.validators import RegexValidator
from django.db.models import Exists, Q
from drf_recaptcha.fields import ReCaptchaV2Field
from rest_framework import serializers

from src.accounts.enums import Language
from src.accounts.models import Account
from src.accounts.serializers.mixins import VacationSerializer
from src.authentication.messages import (
    MSG_AU_0006,
    MSG_AU_0012,
    MSG_AU_0013,
    MSG_AU_0020,
)
from src.generics.fields import (
    DateFormatField,
    TimeStampField,
)
from src.generics.mixins.services import EncryptionMixin
from src.generics.serializers import CustomValidationErrorMixin
from src.authentication.constants import (
    DELEGATION_TTL,
    LOGIN_CODE_TTL,
    PKCE_METHOD,
)
from src.authentication.enums import (
    GrantType,
    TokenEndpointAuthMethod,
)
from src.mcp.enums import (
    HttpMethod,
)
from src.mcp.models import AccessBinding, Connection
from src.generics.serializers import BaseInputSerializer
from src.authentication.tokens import get_expires_in
from src.processes.enums import OwnerRole, OwnerType
from src.processes.models.templates.owner import TemplateOwner

BEARER = 'Bearer'

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


class ContextUserSerializer(
    serializers.ModelSerializer,
):
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
            'manager_id',
            'subordinates_ids',
            'vacation',
        )

    account = ContextAccountSerializer()
    is_supermode = serializers.BooleanField(required=False)
    has_workflow_viewer_access = serializers.SerializerMethodField()
    has_workflow_starter_access = serializers.SerializerMethodField()
    date_joined_tsp = TimeStampField(source='date_joined', read_only=True)
    date_fmt = DateFormatField(read_only=True)
    manager_id = serializers.IntegerField(
        read_only=True,
        allow_null=True,
    )
    subordinates_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        read_only=True,
        source='subordinates',
    )
    vacation = VacationSerializer(read_only=True)

    def get_has_workflow_viewer_access(self, obj) -> bool:
        access = self._get_template_access(obj)
        return access['viewer']

    def get_has_workflow_starter_access(self, obj) -> bool:
        access = self._get_template_access(obj)
        return access['starter']

    def _get_template_access(self, obj) -> dict:
        if hasattr(self, '_template_access_cache'):
            return self._template_access_cache

        user_id = obj.id
        account_id = obj.account_id

        base_qs = TemplateOwner.objects.filter(
            template__account_id=account_id,
            is_deleted=False,
        ).filter(
            Q(type=OwnerType.USER, user_id=user_id)
            | Q(type=OwnerType.GROUP, group__users__id=user_id),
        )
        owner_subq = base_qs.filter(role=OwnerRole.OWNER)
        viewer_subq = base_qs.filter(role=OwnerRole.VIEWER)
        starter_subq = base_qs.filter(role=OwnerRole.STARTER)

        result = (
            UserModel.objects.filter(pk=user_id)
            .annotate(
                has_owner=Exists(owner_subq),
                has_viewer=Exists(viewer_subq),
                has_starter=Exists(starter_subq),
            )
            .values('has_owner', 'has_viewer', 'has_starter')
            .first()
        )

        has_owner = result['has_owner'] if result else False
        has_viewer = result['has_viewer'] if result else False
        has_starter = result['has_starter'] if result else False

        self._template_access_cache = {
            'viewer': has_owner or has_viewer,
            'starter': has_owner or has_viewer or has_starter,
        }
        return self._template_access_cache

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
    read_only_fields = ('id',)
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


class SecuredResetPasswordSerializer(ResetPasswordSerializer):
    captcha = ReCaptchaV2Field()

    def validate(self, attrs):
        attrs = super().validate(attrs)
        attrs.pop('captcha', None)
        return attrs


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


class ResourceSerializer(serializers.Serializer):
    """RFC 8707: a token is requested for exactly the MCP resource."""

    resource = serializers.ListField(child=serializers.CharField())

    def validate_resource(self, value: list[str]) -> list[str]:
        if not settings.MCP_PUBLIC_URL or value != [settings.MCP_PUBLIC_URL]:
            raise serializers.ValidationError
        return value


class AuthorizeSerializer(ResourceSerializer):
    code_challenge_method = serializers.ChoiceField(choices=(PKCE_METHOD,))

    def validate(self, attrs: dict) -> dict:
        if not settings.MCP_ISSUER_URL:
            raise serializers.ValidationError
        return attrs


class ClientRegistrationSerializer(serializers.Serializer):
    """RFC 7591 metadata limited to public or basic-auth code clients."""

    grant_types = serializers.ListField(
        child=serializers.ChoiceField(choices=GrantType.ALLOWED),
        default=[GrantType.AUTHORIZATION_CODE],
    )
    response_types = serializers.ListField(
        child=serializers.CharField(),
        default=['code'],
    )
    token_endpoint_auth_method = serializers.ChoiceField(
        choices=TokenEndpointAuthMethod.ALLOWED,
        default=TokenEndpointAuthMethod.CLIENT_SECRET_BASIC,
    )
    client_name = serializers.CharField(required=False, allow_blank=True)

    def validate_grant_types(self, value: list[str]) -> list[str]:
        if GrantType.AUTHORIZATION_CODE not in value:
            raise serializers.ValidationError
        return value

    def validate_response_types(self, value: list[str]) -> list[str]:
        if value != ['code']:
            raise serializers.ValidationError
        return value

    def validate(self, attrs: dict) -> dict:
        names = self.initial_data.get('client_name', '')
        if not isinstance(names, str):
            raise serializers.ValidationError
        return attrs


class RequestSerializer(BaseInputSerializer):
    request_id = serializers.UUIDField()


class ConsentSerializer(RequestSerializer):
    allow = serializers.BooleanField()


class LoginCompleteSerializer(serializers.Serializer):
    request_id = serializers.UUIDField()
    code = serializers.CharField(max_length=4096, trim_whitespace=False)


class LoginCodeResponseSerializer(serializers.Serializer):
    code = serializers.CharField()
    request_id = serializers.CharField()
    expires_in = serializers.SerializerMethodField()

    def get_expires_in(self, instance) -> int:
        return int(LOGIN_CODE_TTL.total_seconds())


class ConsentContextSerializer(serializers.Serializer):
    request_id = serializers.CharField(source='auth_request.id')
    client = serializers.SerializerMethodField()
    client_id = serializers.CharField(source='application.client_id')
    client_name = serializers.CharField(source='application.name')
    account = serializers.SerializerMethodField()
    user_id = serializers.IntegerField(source='user.pk')
    account_id = serializers.IntegerField(source='user.account_id')
    scopes = serializers.SerializerMethodField()
    expires_at = serializers.SerializerMethodField()
    login_complete = serializers.SerializerMethodField()

    def get_client(self, instance) -> dict:
        return {
            'id': instance.application.client_id,
            'name': instance.application.name,
        }

    def get_account(self, instance) -> dict:
        return {
            'id': instance.user.account_id,
            'name': instance.user.account.name,
        }

    def get_scopes(self, instance) -> list[str]:
        return instance.auth_request.parameters['scope'].split()

    def get_expires_at(self, instance) -> str:
        return instance.auth_request.expires_at.isoformat()

    def get_login_complete(self, instance) -> bool:
        return instance.auth_request.login_completed_at is not None


class IntrospectionSerializer(BaseInputSerializer):
    token = serializers.CharField(max_length=4096, trim_whitespace=False)
    resource = serializers.CharField(max_length=2048)


class DelegationSerializer(IntrospectionSerializer):
    tool = serializers.CharField(max_length=80)
    method = serializers.ChoiceField(choices=HttpMethod.DELEGATION_CHOICES)
    path = serializers.CharField(max_length=8192)
    scopes = serializers.ListField(
        child=serializers.CharField(max_length=80),
        required=False,
    )


class IntrospectionResponseSerializer(serializers.ModelSerializer):
    """RFC 7662 response for an active token; inactive is `active: false`."""

    class Meta:
        model = AccessBinding
        fields = (
            'active',
            'client_id',
            'user_id',
            'account_id',
            'connection_id',
            'scope',
            'aud',
            'exp',
        )

    active = serializers.SerializerMethodField()
    client_id = serializers.CharField(
        source='connection.application.client_id',
    )
    user_id = serializers.IntegerField(source='connection.user_id')
    account_id = serializers.IntegerField(source='connection.account_id')
    connection_id = serializers.CharField(source='connection.id')
    scope = serializers.CharField(source='access_token.scope')
    aud = serializers.SerializerMethodField()
    exp = serializers.SerializerMethodField()

    def get_active(self, instance: AccessBinding) -> bool:
        return True

    def get_aud(self, instance: AccessBinding) -> list[str]:
        return [instance.connection.resource]

    def get_exp(self, instance: AccessBinding) -> int:
        return int(instance.access_token.expires.timestamp())


class DelegationResponseSerializer(serializers.Serializer):
    credential = serializers.CharField()
    token_type = serializers.SerializerMethodField()
    expires_in = serializers.SerializerMethodField()
    expires_at = serializers.SerializerMethodField()
    audience = serializers.CharField(source='delegation.audience')
    operation = serializers.CharField(source='delegation.operation')
    scopes = serializers.ListField(source='delegation.scopes')
    connection_id = serializers.CharField(source='delegation.connection_id')
    user_id = serializers.IntegerField(source='delegation.connection.user_id')
    account_id = serializers.IntegerField(
        source='delegation.connection.account_id',
    )

    def get_token_type(self, instance) -> str:
        return BEARER

    def get_expires_in(self, instance) -> int:
        return get_expires_in(
            expires_at=instance.delegation.expires_at,
            ttl=DELEGATION_TTL,
        )

    def get_expires_at(self, instance) -> int:
        return int(instance.delegation.expires_at.timestamp())


class ConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Connection
        fields = (
            'id',
            'client_id',
            'client_name',
            'scopes',
            'created_at',
            'revoked_at',
            'user_id',
            'account_id',
        )

    client_id = serializers.CharField(source='application.client_id')
    client_name = serializers.CharField(source='application.name')
    created_at = serializers.SerializerMethodField()
    revoked_at = serializers.SerializerMethodField()
    user_id = serializers.IntegerField()
    account_id = serializers.IntegerField()

    def get_created_at(self, instance: Connection) -> str:
        return instance.created_at.isoformat()

    def get_revoked_at(self, instance: Connection) -> str | None:
        if instance.revoked_at is None:
            return None
        return instance.revoked_at.isoformat()
