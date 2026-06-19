from django_filters.rest_framework import FilterSet

from src.generics.filters import DefaultOrderingFilter
from src.datasets.models import Dataset


class DatasetFilter(FilterSet):
    ordering = DefaultOrderingFilter(
        fields=(
            ('name', 'name'),
            ('date_created', 'date'),
        ),
        default=('-date_created',),
    )

    class Meta:
        model = Dataset
        fields = (
            'ordering',
        )
