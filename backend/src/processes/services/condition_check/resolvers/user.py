from .base import Resolver


class UserResolver(Resolver):
    def _prepare_args(self):
        self.predicate_value = (
            int(self._predicate.value)
            if self._predicate.value
            else None
        )
        field = self._get_field()
        self.field_value = field.user_id or None
