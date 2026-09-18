from .base import Resolver


class FileResolver(Resolver):
    def _prepare_args(self):
        field = self._get_field()
        self.field_value = field.storage_attachments.exists() or None
