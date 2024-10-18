# pylint: disable=unsupported-membership-test
from typing import Optional
from django_filters.rest_framework import (
    DjangoFilterBackend,
    FilterSet,
    OrderingFilter,
    Filter
)
from django_filters import CharFilter
from django_filters.constants import EMPTY_VALUES
from django.contrib.postgres.search import SearchQuery
from rest_framework.viewsets import ViewSet
from rest_framework.serializers import ValidationError

from pneumatic_backend.generics.querysets import BaseQuerySet
from pneumatic_backend.generics.messages import MSG_GE_0001


class PneumaticFilterBackend(DjangoFilterBackend):
    def _set_filterset_class(self, view):
        action_filterset_class = view.action_filterset_classes[view.action]
        setattr(view, 'filterset_class', action_filterset_class)

    def get_filterset_class(
        self,
        view: ViewSet,
        queryset: BaseQuerySet,
    ) -> Optional[FilterSet]:
        has_action_filter = (
            hasattr(view, 'action_filterset_classes') and
            view.action in view.action_filterset_classes
        )
        if has_action_filter:
            self._set_filterset_class(view)
        return super().get_filterset_class(view, queryset)


class PneumaticBaseFilterSet(FilterSet):
    def filter_queryset(self, queryset: BaseQuerySet):
        queryset = super().filter_queryset(queryset)
        return queryset.combine_filters()


class DefaultOrderingFilter(OrderingFilter):

    def __init__(self, *args, default=None, **kwargs):
        self.default = default
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        value = value or self.default
        return super().filter(qs, value)


class ListFilter(Filter):

    """ Accepts a list of values separated by commas.
        Example: 'val_1, val_1'

        Need to specify lookup_expr for filtering qst by values. For example
        value = 'val_1, val_1' and lookup_expr='in' then qst will be
        filtered as MyModel.objects.filter(field_name__in=[val_1,val_1])

        Parameters:
            - choices: Tuple[Tuple[<value>,<verbose name>]] -
              a list allowed values.
            - map_to_db: Dict[value, new_value] - maps values to new values.
              For example:  value = 'val_1, val_2'
                and map_to_db = {'val_1': 'new_val_1'}
                then qst will be filtered as
                MyModel.objects.filter(field_name__in=[new_val_1,val_2] """

    def __init__(self, *args, choices=None, map_to_db=None, **kwargs):
        self.map_to_db = map_to_db
        self.allowed_values = set(
            str(choice[0]) for choice in choices
        ) if choices else None
        super().__init__(*args, **kwargs)

    def validate(self, values: set):
        if self.allowed_values:
            for elem in values:
                if elem not in self.allowed_values:
                    raise ValidationError(MSG_GE_0001(elem))

    def _perform_mapping_values(self, values: set) -> set:
        if self.map_to_db:
            values = {self.map_to_db.get(value, value) for value in values}
        return values

    def filter(self, qs, value):
        if value in EMPTY_VALUES:
            return qs
        values = set(value.replace(' ', '').split(','))
        self.validate(values)
        values = self._perform_mapping_values(values)
        qs = super().filter(qs, values)
        return qs


class TsQuerySearchFilter(CharFilter):

    """ Allow search by word prefix by :*
        Allow union search result from different words """

    def filter(self, qs, value):
        if value in EMPTY_VALUES:
            return qs
        words = [f'{word}:*' for word in value.split(' ')]
        value = ' | '.join(words)
        value = SearchQuery(
            value=value,
            search_type='raw'
        )
        return super().filter(qs, value)
