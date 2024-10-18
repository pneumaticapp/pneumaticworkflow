# pylint:disable=protected-access
from django.db import models
from django.db.models import ProtectedError, QuerySet


class SoftDeleteMixin:

    def _on_delete(self, **kwargs):
        model = self.model if isinstance(self, QuerySet) else self
        for relation in model._meta._relation_tree:
            on_delete = getattr(
                relation.remote_field,
                'on_delete',
                models.DO_NOTHING,
            )
            if on_delete in [None, models.DO_NOTHING]:
                continue

            relation_filter = (
                {f'{relation.name}__in': self} if isinstance(self, QuerySet)
                else {relation.name: self}
            )
            related_queryset = relation.model.objects.filter(**relation_filter)
            if on_delete is models.CASCADE:
                related_queryset.delete(**kwargs)

            elif on_delete is models.SET_NULL:
                related_queryset.update(**{relation.name: None})
            elif on_delete is models.PROTECT:
                if related_queryset.count() > 0:
                    raise ProtectedError(
                        msg=f'Cannot delete {self._meta.object_name}',
                        protected_objects=None,
                    )
            else:
                raise NotImplementedError()
