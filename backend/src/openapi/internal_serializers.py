"""Schema-only contracts for authentication and product support endpoints."""

from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer

from src.accounts.enums import UserGroupType
from src.accounts.serializers.api_key import APIKeySerializer
from src.accounts.serializers.public.accounts import PublicAccountSerializer
from src.ai.enums import AIVendor
from src.ai.serializers import AIProviderSerializer
from src.authentication.serializers import (
    SecuredResetPasswordSerializer,
    SecuredSignUpSerializer,
)
from src.notifications.serializers import DeviceSerializer
from src.payment.serializers import CardSetupSerializer, PurchaseSerializer


class CardSetupQuerySerializer(CardSetupSerializer):
    """Both return URLs are needed by the real Stripe service call."""

    cancel_url = serializers.URLField(
        required=True,
        allow_null=True,
        allow_blank=False,
    )


@extend_schema_serializer(component_name='Purchase')
class PurchaseRequestSerializer(PurchaseSerializer):
    """Both return URLs are required by the unchanged purchase service."""

    cancel_url = serializers.URLField(
        required=True,
        allow_null=True,
        allow_blank=False,
    )


class GroupCreateResponseSerializer(serializers.Serializer):
    """Group creation returns validated input, without the new group ID."""

    name = serializers.CharField()
    photo = serializers.CharField(allow_blank=True)
    users = serializers.ListField(
        child=serializers.IntegerField(), required=False,
    )
    type = serializers.ChoiceField(
        choices=UserGroupType.CHOICES, required=False,
    )


class APIKeyReadResponseSerializer(APIKeySerializer):
    class Meta(APIKeySerializer.Meta):
        fields = tuple(
            name for name in APIKeySerializer.Meta.fields if name != 'token'
        )


class CredentialsRequestSerializer(serializers.Serializer):
    username = serializers.CharField(help_text='The account email address.')
    password = serializers.CharField(write_only=True)


class AIProviderResponseSerializer(AIProviderSerializer):
    vendor = serializers.ChoiceField(
        choices=[*AIVendor.CHOICES, (AIVendor.CUSTOM, 'Custom')],
        read_only=True,
    )


class SignUpRequestSerializer(SecuredSignUpSerializer):
    captcha = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text=(
            'reCAPTCHA response. Required only when GET /auth/signup returns '
            'show_captcha=true; otherwise ignored and may be omitted, empty '
            'or null.'
        ),
    )


class PasswordResetRequestSerializer(SecuredResetPasswordSerializer):
    captcha = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text=(
            'reCAPTCHA response. Required only when GET /auth/reset-password/'
            'captcha returns show_captcha=true; otherwise ignored and may '
            'be omitted, empty or null.'
        ),
    )


class SignupCaptchaResponseSerializer(serializers.Serializer):
    show_captcha = serializers.BooleanField()


@extend_schema_serializer(many=False)
class PublicAccountResponseSerializer(PublicAccountSerializer):
    language = serializers.CharField(read_only=True)
    timezone = serializers.CharField(read_only=True)
    date_fmt = serializers.CharField(read_only=True)
    date_fdw = serializers.IntegerField(read_only=True)


class AuthUriResponseSerializer(serializers.Serializer):
    auth_uri = serializers.URLField(
        help_text='Redirect the browser here, preserving provider state.',
    )


class EmailAddressSerializer(serializers.Serializer):
    email = serializers.EmailField()


class InviteIdResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()


class InviteUsersResponseSerializer(serializers.Serializer):
    already_accepted = EmailAddressSerializer(
        many=True,
        help_text='Previously accepted invitees; an empty array on success.',
    )


class DeclineInviteRequestSerializer(serializers.Serializer):
    invite_id = serializers.UUIDField()


class NotificationsReadRequestSerializer(serializers.Serializer):
    notifications = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text=(
            "Notification IDs to mark read. Only the current user's unread "
            'notifications are updated. Omitted/empty list is a no-op.'
        ),
    )


class DeviceRegistrationRequestSerializer(DeviceSerializer):
    class Meta(DeviceSerializer.Meta):
        extra_kwargs = {
            'user': {'required': False},
            'description': {'required': False},
            'is_app': {'required': False},
        }


class PaymentLinkResponseSerializer(serializers.Serializer):
    payment_link = serializers.URLField()


class SetupLinkResponseSerializer(serializers.Serializer):
    setup_link = serializers.URLField()


class CustomerPortalResponseSerializer(serializers.Serializer):
    link = serializers.URLField()


class PaymentCardResponseSerializer(serializers.Serializer):
    last4 = serializers.CharField()
    brand = serializers.CharField()


# Raw schemas preserve the actual empty object and arbitrary JSON body.
# An empty Serializer would otherwise be removed as an empty component.
EMPTY_OBJECT_SCHEMA = {'type': 'object', 'additionalProperties': False}
JSON_VALUE_SCHEMA = {
    'oneOf': [
        {
            'type': 'object',
            'additionalProperties': True,
            'nullable': True,
        },
        {'type': 'array', 'items': {}},
        {'type': 'string'},
        {'type': 'number'},
        {'type': 'boolean'},
    ],
}
