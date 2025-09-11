from django_filters import (
    ChoiceFilter,
    BooleanFilter,
    OrderingFilter,
)
from django_filters.rest_framework import (
    IsoDateTimeFilter,
    FilterSet,
)
from django_filters.constants import EMPTY_VALUES

from src.generics.filters import (
    TsQuerySearchFilter,
    DefaultOrderingFilter
)
from src.processes.enums import TaskStatus, WorkflowStatus
from src.processes.models import (
    Template,
    SystemTemplate,
    WorkflowEvent,
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


class WorkflowWebhookFilterSet(FilterSet):

    status = ChoiceFilter(
        choices=(
            (WorkflowStatus.RUNNING, WorkflowStatus.RUNNING),
            (WorkflowStatus.DONE, WorkflowStatus.DONE),
        ),
    )
    ordering = DefaultOrderingFilter(
        fields=(
            ('date_created', 'date_created'),
            ('-date_created', '-date_created'),
        ),
        default=('-date_created',)
    )


class TaskWebhookFilterSet(FilterSet):

    status = ChoiceFilter(
        choices=(
            (TaskStatus.ACTIVE, TaskStatus.ACTIVE),
            (TaskStatus.COMPLETED, TaskStatus.COMPLETED),
        ),
    )
    ordering = DefaultOrderingFilter(
        fields=(
            ('date_started', 'date_started'),
            ('-date_started', '-date_started'),
        ),
        default=('-date_started',)
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
    only_attachments = BooleanFilter(method='filter_only_attachments')

    def filter_comments(self, queryset, name, value):
        if not value:
            return queryset.exclude_comments()

        return queryset

    def filter_only_attachments(self, queryset, name, value):
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
