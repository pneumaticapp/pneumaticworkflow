from decimal import Decimal

from .base import Resolver


class NumberResolver(Resolver):
    def _prepare_args(self):
        self.predicate_value = (
            Decimal(self._predicate.value) if self._predicate.value else None
        )
        field = self._get_field()
        self.field_value = Decimal(field.value) if field.value else None
