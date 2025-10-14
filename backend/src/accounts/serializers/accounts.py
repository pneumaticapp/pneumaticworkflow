from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from src.accounts.models import Account
from src.generics.serializers import CustomValidationErrorMixin
from src.accounts.messages import MSG_A_0003
from src.generics.fields import TimeStampField


UserModel = get_user_model()


class AccountCacheSerializer(serializers.ModelSerializer):

    class Meta:
        model = Account
        fields = (
            'active_users',
            'tenants_active_users',
        )


class AccountSerializer(
    CustomValidationErrorMixin,
    serializers.ModelSerializer,
):

    class Meta:
        model = Account
        fields = (
            'id',
            'date_joined',
            'date_joined_tsp',
            'plan_expiration',
            'plan_expiration_tsp',
            'lease_level',
            'name',
            'logo_lg',
            'logo_sm',
        )
        read_only_fields = (
            'id',
            'date_joined',
            'date_joined_tsp',
            'plan_expiration',
            'plan_expiration_tsp',
            'lease_level',
        )

    date_joined_tsp = TimeStampField(
        source='date_joined',
        read_only=True,
    )
    plan_expiration_tsp = TimeStampField(
        source='plan_expiration',
        read_only=True,
    )

    def validate_logo_lg(self, value):
        if value and self.instance.is_tenant:
            raise ValidationError(MSG_A_0003)
        return value

    def validate_logo_sm(self, value):
        if value and self.instance.is_tenant:
            raise ValidationError(MSG_A_0003)
        return value


class AccountPlanSerializer(serializers.ModelSerializer):

    class Meta:
        model = Account
        fields = (
            'is_subscribed',
            'active_users',
            'tenants_active_users',
            'max_users',
            'billing_sync',
            'billing_plan',
            'billing_period',
            'plan_expiration',
            'plan_expiration_tsp',
            'trial_is_active',
            'trial_ended',
        )

    plan_expiration_tsp = TimeStampField(
        read_only=True,
        source='plan_expiration',
    )
