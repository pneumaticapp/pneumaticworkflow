from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from drf_recaptcha.fields import ReCaptchaV2Field
from django.core.validators import RegexValidator
from pneumatic_backend.accounts.models import Account
from pneumatic_backend.generics.fields import TimeStampField, DateFormatField
from pneumatic_backend.generics.serializers import CustomValidationErrorMixin
from pneumatic_backend.accounts.enums import (
    BillingPlanType,
    Language,
)
from pneumatic_backend.authentication.messages import (
    MSG_AU_0013,
    MSG_AU_0012,
    MSG_AU_0006,
)


UserModel = get_user_model()


class SignUpSerializer(
    CustomValidationErrorMixin,
    serializers.ModelSerializer
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
            RegexValidator(regex=r'^\+?\d{9,16}$', message=MSG_AU_0006)
        ]
    )
    password = serializers.CharField(
        required=False,
        allow_null=True,
        min_length=6
    )
    company_name = serializers.CharField(required=False)
    language = serializers.ChoiceField(
        choices=Language.EURO_CHOICES,
        required=False
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
            'captcha'
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
            'max_templates',
            'active_templates',
            'payment_card_provided',
            'is_subscribed',
            'billing_plan',
            'billing_sync',
            'billing_period',
            'plan_expiration',
            'plan_expiration_tsp',
            'trial_is_active',
            'trial_ended',
        )

    max_templates = serializers.SerializerMethodField()
    date_joined_tsp = TimeStampField(source='date_joined', read_only=True)
    plan_expiration_tsp = TimeStampField(
        source='plan_expiration',
        read_only=True
    )

    def get_max_templates(self, instance: Account):
        if instance.billing_plan != BillingPlanType.FREEMIUM:
            return None
        return instance.max_active_templates


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
            'is_staff',
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
        )

    account = ContextAccountSerializer()
    # TODO Remove in https://my.pneumatic.app/workflows/34238/
    is_staff = serializers.BooleanField(source='is_admin', read_only=True)
    is_supermode = serializers.BooleanField(required=False)
    date_joined_tsp = TimeStampField(source='date_joined', read_only=True)
    date_fmt = DateFormatField(read_only=True)

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
        'is_active'
    )
    read_only_fields = ('id', )
    extra_kwargs = {
        'email': {'validators': []}
    }


class SignInWithGoogleSerializer(serializers.Serializer):
    email = serializers.EmailField()


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
    serializers.Serializer
):

    code = serializers.CharField(
        allow_null=False,
        allow_blank=False,
        required=True
    )
    state = serializers.CharField(
        allow_null=False,
        allow_blank=False,
        required=True
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
        required=True
    )
    client_info = serializers.CharField(
        allow_null=False,
        allow_blank=False,
        required=True
    )


class Auth0TokenSerializer(AuthTokenSerializer):

    pass


class TokenSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer
):
    token = serializers.CharField(
        required=True,
        allow_null=False,
        allow_blank=False
    )


class ResetPasswordSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer
):
    email = serializers.EmailField(required=True)


class ConfirmPasswordSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer
):
    new_password = serializers.CharField()
    confirm_new_password = serializers.CharField()
    token = serializers.CharField(
        required=True,
        allow_null=False,
        allow_blank=False
    )

    def validate(self, attrs):
        if attrs.get('new_password') != attrs.get('confirm_new_password'):
            raise serializers.ValidationError(MSG_AU_0013)
        return attrs


class ChangePasswordSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer
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
