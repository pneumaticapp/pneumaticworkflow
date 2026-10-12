from .base import Resolver


class DropdownResolver(Resolver):
    def _prepare_args(self):
        field = self._get_field()
        self.field_value = field.value or None
        self.predicate_value = self._predicate.value
