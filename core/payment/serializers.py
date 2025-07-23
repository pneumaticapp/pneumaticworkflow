from rest_framework import serializers
from rest_framework.serializers import ValidationError
from rest_framework_simplejwt.tokens import TokenError
from pneumatic_backend.generics.mixins.serializers import (
    CustomValidationErrorMixin
)
from pneumatic_backend.payment.stripe.tokens import ConfirmToken
from pneumatic_backend.payment.models import Product, Price
from pneumatic_backend.payment.messages import (
    MSG_BL_0001,
    MSG_BL_0002,
    MSG_BL_0003,
)


class PriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Price
        fields = (
            'name',
            'code',
            'max_quantity',
            'min_quantity',
            'status',
            'price_type',
            'price',
            'currency',
            'trial_days',
            'billing_period',
        )


class ProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = (
            'name',
            'code',
            'is_subscription',
            'prices',
        )

    prices = PriceSerializer(many=True)


class PurchaseProductSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer
):

    code = serializers.CharField(
        required=True,
        allow_null=False,
        allow_blank=False,
    )
    quantity = serializers.IntegerField(
        required=True,
        allow_null=False,
        min_value=1,
    )


class PurchaseSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer
):

    success_url = serializers.URLField(
        required=True,
        allow_null=False,
        allow_blank=False
    )
    cancel_url = serializers.URLField(
        required=False,
        allow_null=True,
        allow_blank=False
    )
    products = PurchaseProductSerializer(
        many=True,
        required=True,
        allow_null=False,
    )

    def validate_products(self, attrs):
        if not attrs:
            raise ValidationError(MSG_BL_0002)
        request_codes = {elem['code'] for elem in attrs}
        existent_codes = {
            elem for elem in Price.objects.active_or_archived().filter(
                code__in=request_codes
            ).order_by('code').values_list('code', flat=True)
        }
        non_existent_codes = request_codes - existent_codes
        if non_existent_codes:
            raise ValidationError(MSG_BL_0003(non_existent_codes))
        return attrs


class CardSetupSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer
):

    success_url = serializers.URLField(
        required=True,
        allow_null=False,
        allow_blank=False
    )
    cancel_url = serializers.URLField(
        required=False,
        allow_null=True,
        allow_blank=False
    )


class ConfirmSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer
):
    token = serializers.CharField(
        required=True,
        allow_null=False,
        allow_blank=False,
    )

    def validate_token(self, value) -> ConfirmToken:
        try:
            token = ConfirmToken(value)
        except TokenError:
            raise ValidationError(MSG_BL_0001)
        else:
            return token


class CustomerPortalSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer
):

    cancel_url = serializers.URLField(
        required=True,
        allow_null=False,
        allow_blank=False
    )
