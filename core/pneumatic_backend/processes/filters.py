# pylint:disable=unused-argument
from django_filters import (
    ChoiceFilter,
    BooleanFilter,
    NumberFilter,
    OrderingFilter,
)
from django_filters.rest_framework import (
    IsoDateTimeFilter,
    FilterSet,
)
from django_filters.constants import EMPTY_VALUES
from pneumatic_backend.generics.filters import (
    TsQuerySearchFilter
)
from pneumatic_backend.generics.filters import PneumaticBaseFilterSet
from pneumatic_backend.processes.enums import (
    WorkflowApiStatus,
)
from pneumatic_backend.processes.models import (
    Template,
    Workflow,
    SystemTemplate,
    WorkflowEvent,
)
from pneumatic_backend.generics.filters import (
    ListFilter
)


class TemplateOrderingFilter(OrderingFilter):
    def filter(self, qs, value):
        ordering = ['-is_active']
        if value not in EMPTY_VALUES:
            ordering.extend(value)

        return super().filter(qs, ordering)


class TemplateFilter(FilterSet):
    ordering = TemplateOrderingFilter(
        fields=(
            ('name', 'name'),
            ('date_created', 'date')
        )
    )

    class Meta:
        model = Template
        fields = (
            'ordering',
            'is_active',
        )


class WorkflowDurationFilter(FilterSet):
    date_from = IsoDateTimeFilter(method='filter_date_from')
    date_to = IsoDateTimeFilter(method='filter_date_to')

    def filter_date_from(self, queryset, name, value):
        if value:
            return queryset.workflows_updated_from(value, as_combine=True)
        return queryset

    def filter_date_to(self, queryset, name, value):
        if value:
            return queryset.workflows_updated_to(value, as_combine=True)
        return queryset


class WorkflowSuccessRateFilter(FilterSet):
    date_from = IsoDateTimeFilter(method='filter_date_from')
    date_to = IsoDateTimeFilter(method='filter_date_to')

    def filter_date_from(self, queryset, name, value):
        if value:
            return queryset.workflows_updated_from(value, as_combine=True)
        return queryset

    def filter_date_to(self, queryset, name, value):
        if value:
            return queryset.workflows_updated_to(value, as_combine=True)
        return queryset


class RecentTaskFilter(FilterSet):
    status = ChoiceFilter(
        choices=(
            ('running', 'running'),
            ('completed', 'completed'),
        ),
        method='filter_status',
    )

    def filter_status(self, queryset, name, value):
        if value == 'running':
            return queryset.running_now().order_by('-date_started')
        if value == 'completed':
            return queryset.completed().order_by('-date_completed')

        return queryset


class WorkflowFieldsFilter(PneumaticBaseFilterSet):

    class Meta:
        model = Workflow
        fields = (
            'template_id',
            'status',
            'fields'
        )

    template_id = NumberFilter(
        field_name='template_id',
        required=True,
    )
    status = ListFilter(
        field_name='status',
        lookup_expr='in',
        choices=WorkflowApiStatus.CHOICES,
        map_to_db=WorkflowApiStatus.MAP,
    )

    fields = ListFilter(
        field_name='fields__api_name',
        lookup_expr='in',
        distinct=True,
    )


class WorkflowEventFilter(FilterSet):

    class Meta:
        model = WorkflowEvent
        fields = (
            'ordering',
            'include_comments',
            'only_attachments',
        )

    ordering = OrderingFilter(
        fields=(
            ('created', 'created'),
        )
    )
    include_comments = BooleanFilter(method='filter_comments')
    only_attachments = BooleanFilter(method='filter_timeline')

    def filter_comments(self, queryset, name, value):
        if not value:
            return queryset.exclude_comments()

        return queryset

    def filter_timeline(self, queryset, name, value):
        if value:
            return queryset.only_with_attachments().distinct()
        return queryset


class SystemTemplateFilter(FilterSet):

    class Meta:
        model = SystemTemplate
        fields = (
            'category',
            'search'
        )

    search = TsQuerySearchFilter(
        field_name='search_content',
    )
