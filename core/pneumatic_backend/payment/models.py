from django.db import models
from pneumatic_backend.payment.enums import (
    PriceType,
    BillingPeriod,
    PriceStatus,
)
from pneumatic_backend.payment.querysets import (
    PriceQuerySet,
    ProductQuerySet
)
from pneumatic_backend.generics.managers import BaseSoftDeleteManager
from pneumatic_backend.generics.models import SoftDeleteModel


class Product(SoftDeleteModel):

    class Meta:
        ordering = ('id',)

    name = models.CharField(max_length=500)
    code = models.CharField(
        max_length=100,
        unique=True,
        help_text=(
            'Used to identify the product. '
            'Available values: "fractionalcoo", "premium", "unlimited"'
        ),
        null=True  # TODO remove
    )
    is_subscription = models.BooleanField(
        help_text='Set to true if the product is subscription'
    )
    stripe_id = models.CharField(max_length=250, unique=True, null=True)
    is_active = models.BooleanField(
        help_text='False if product archived'
    )

    objects = BaseSoftDeleteManager.from_queryset(ProductQuerySet)()

    def __str__(self):
        return self.name


class Price(SoftDeleteModel):

    class Meta:
        ordering = ('product_id', 'id',)

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='prices'
    )
    status = models.CharField(
        max_length=255,
        choices=PriceStatus.CHOICES,
        help_text=(
            '"Archived" status allows only update, '
            '"inactive" disables the price'
        )
    )
    name = models.CharField(max_length=500)
    code = models.CharField(
        max_length=100,
        unique=True,
        help_text='Used to identify the product price'
    )
    stripe_id = models.CharField(max_length=250, unique=True)
    max_quantity = models.PositiveIntegerField(
        help_text=(
            'Limit the maximum quantity to buy. '
            'You can specify a value up to 10000'
        )
    )
    min_quantity = models.PositiveIntegerField(
        help_text='Minimum quantity, must be less then the "max_quantity"'
    )
    price_type = models.CharField(choices=PriceType.CHOICES, max_length=50)
    price = models.PositiveIntegerField(help_text='in cents')
    currency = models.CharField(max_length=10)
    trial_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='For "Recurring" price type only',
    )
    billing_period = models.CharField(
        max_length=100,
        choices=BillingPeriod.CHOICES,
        help_text='For "Recurring" price type only',
        blank=True,
        null=True
    )

    objects = BaseSoftDeleteManager.from_queryset(PriceQuerySet)()

    def __str__(self):
        return self.name

    @property
    def is_archived(self):
        return self.status == PriceStatus.ARCHIVED
