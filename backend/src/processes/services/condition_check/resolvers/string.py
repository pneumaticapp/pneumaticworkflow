from .base import Resolver


class StringResolver(Resolver):
    def _prepare_args(self):
        self.predicate_value = self._predicate.value
        field = self._get_field()
        self.field_value = field.value or None
