from django.db.models import QuerySet
from pneumatic_backend.payment.enums import (
    PriceType,
    PriceStatus,
)


class ProductQuerySet(QuerySet):

    def active(self):
        return self.filter(is_active=True)


class PriceQuerySet(QuerySet):

    def active(self):
        return self.filter(
            status=PriceStatus.ACTIVE,
            product__is_active=True
        )

    def active_or_archived(self):
        return self.filter(
            status__in=(PriceStatus.ACTIVE, PriceStatus.ARCHIVED),
            product__is_active=True
        )

    def subscriptions(self):
        return self.filter(
            price_type=PriceType.RECURRING,
            product__is_subscription=True
        )

    def not_subscriptions(self):
        return self.filter(product__is_subscription=False)

    def by_code(self, code: str):
        return self.filter(code=code)
