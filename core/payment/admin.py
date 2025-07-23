from django.contrib import admin
from pneumatic_backend.payment.models import (
    Price,
    Product
)
from pneumatic_backend.payment.forms import PriceInlineForm


@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):

    model = Price
    exclude = ('is_deleted',)
    readonly_fields = (
        'product',
        'name',
        'stripe_id',
        'price_type',
        'price',
        'currency',
        'billing_period',
    )
    list_display = (
        'name',
        'status',
        'stripe_id',
    )
    list_filter = (
        'product',
        'billing_period',
        'status',
        'price_type',
    )

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class PriceInline(admin.StackedInline):

    model = Price
    form = PriceInlineForm
    extra = 0
    min_num = 1
    exclude = ('is_deleted',)
    readonly_fields = (
        'name',
        'stripe_id',
        'price_type',
        'price',
        'currency',
        'billing_period',
    )

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    model = Product
    inlines = (PriceInline,)
    exclude = ('is_deleted',)
    list_display = (
        'name',
        'is_subscription',
        'is_active',
    )
    readonly_fields = (
        'name',
        'stripe_id',
        'is_active',
    )

    def has_add_permission(self, obj):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
