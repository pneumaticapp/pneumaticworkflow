from .base import Resolver


class GroupResolver(Resolver):
    def _prepare_args(self):
        self.predicate_value = (
            int(self._predicate.value)
            if self._predicate.value
            else None
        )
        field = self._get_field()
        self.field_value = field.group_id or None
