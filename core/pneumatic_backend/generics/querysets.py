from typing import List, Optional
from django.db import transaction
from django.db.models import QuerySet, Q
from pneumatic_backend.generics.mixins.models import SoftDeleteMixin
from pneumatic_backend.queries import SqlQueryObject


class BaseQuerySet(SoftDeleteMixin, QuerySet):
    _custom_filter_props = set()

    def __init__(self, *args, **kwargs):
        self._custom_filter_props.add('_q_filters')
        self._q_filters = Q()
        super().__init__(*args, **kwargs)

    # pylint:disable=protected-access
    def _clone(self):
        c = super()._clone()
        for _filter_props in self._custom_filter_props:
            _filter = getattr(self, _filter_props, None)
            if _filter is not None:
                setattr(c, _filter_props, _filter)
        return c

    def _add_filter(
            self,
            filter_: Q,
            as_combine: bool = False,
            attrname: str = '_q_filters',
    ):
        if as_combine:
            attr_filter = getattr(self, attrname)
            attr_filter &= filter_
            setattr(self, attrname, attr_filter)
            return self
        return self.filter(filter_)

    def combine_filters(self):
        return self.filter(self._q_filters)

    def execute_raw(
        self,
        query: SqlQueryObject,
        using: Optional[str] = None
    ):
        query, raw_params = query.get_sql()
        return self.raw(query, raw_params, using=using)

    def by_id(self, pk):
        return self.filter(id=pk)

    def by_ids(self, ids):
        return self.filter(id__in=ids)

    def only_ids(self):
        return self.values_list('id', flat=True)

    @transaction.atomic
    def delete(self, **kwargs):
        self._on_delete(**kwargs)
        return self.filter(**kwargs).update(is_deleted=True)


class BaseHardQuerySet(QuerySet):
    def execute_raw(self, query: SqlQueryObject):
        query, raw_params = query.get_sql()
        return self.raw(query, raw_params)

    def by_id(self, pk):
        return self.filter(id=pk)

    def by_ids(self, ids: List[int]):
        return self.filter(id__in=ids)

    def exclude_ids(self, ids: List[int]):
        return self.exclude(id__in=ids)


class AccountBaseQuerySet(BaseQuerySet):
    def on_account(self, account_id: int):
        return self.filter(account_id=account_id)
