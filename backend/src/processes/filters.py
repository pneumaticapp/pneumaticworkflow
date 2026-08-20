from django_filters import (
    BooleanFilter,
    ChoiceFilter,
    OrderingFilter,
)
from django_filters.constants import EMPTY_VALUES
from django_filters.rest_framework import FilterSet

from src.generics.filters import (
    DefaultOrderingFilter,
    TsQuerySearchFilter,
)
from src.processes.enums import TaskStatus, WorkflowStatus
from src.processes.models.templates.fieldset import FieldsetTemplate
from src.processes.models.templates.system_template import SystemTemplate
from src.processes.models.workflows.event import WorkflowEvent


class TemplateOrderingFilter(OrderingFilter):
    def filter(self, qs, value):
        ordering = ['-is_active']
        if value not in EMPTY_VALUES:
            ordering.extend(value)

        return super().filter(qs, ordering)


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
        default=('-date_created',),
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
        default=('-date_started',),
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
        ),
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
            'search',
        )

    search = TsQuerySearchFilter(
        field_name='search_content',
    )


class FieldSetFilter(FilterSet):

    ordering = DefaultOrderingFilter(
        fields=(
            ('name', 'name'),
            ('date_created', 'date'),
        ),
        default=('-date_created',),
    )

    class Meta:
        model = FieldsetTemplate
        fields = (
            'ordering',
        )
