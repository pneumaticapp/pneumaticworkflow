from abc import abstractmethod
from pneumatic_backend.generics.models import SoftDeleteModel
from pneumatic_backend.processes.models.mixins import ApiNameMixin
from pneumatic_backend.processes.utils.common import create_api_name


class BaseApiNameModel(
    SoftDeleteModel,
    ApiNameMixin
):

    class Meta:
        abstract = True

    @property
    @abstractmethod
    def api_name_prefix(self) -> str:
        pass

    def _create_api_name(self):
        return create_api_name(self.api_name_prefix)

    def save(self, update_fields=None, **kwargs):
        self.api_name = self.api_name or self._create_api_name()
        if update_fields is not None and 'api_name' not in update_fields:
            update_fields.append('api_name')
        super().save(update_fields=update_fields, **kwargs)
