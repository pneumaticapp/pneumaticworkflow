from django_filters import ChoiceFilter
from django_filters.rest_framework import (
    FilterSet,
)
from pneumatic_backend.generics.filters import (
    DefaultOrderingFilter,
    ListFilter
)
from pneumatic_backend.accounts.enums import (
    NotificationStatus,
    UserType,
    UserStatus,
    SourceType,
)
from pneumatic_backend.accounts.models import (
    Notification,
    User,
    Account,
    Contact,
)
from pneumatic_backend.generics.filters import (
    TsQuerySearchFilter
)
from pneumatic_backend.accounts.models import UserGroup


class NotificationFilter(FilterSet):
    status = ChoiceFilter(choices=NotificationStatus.CHOICES)

    class Meta:
        model = Notification
        fields = ('status', )


class UsersListFilterSet(FilterSet):

    class Meta:
        model = User
        fields = (
            'status',
            'type',
            'ordering',
            'groups',
        )

    ordering = DefaultOrderingFilter(
        fields=(
            ('first_name', 'first_name'),
            ('last_name', 'last_name'),
            ('status', 'status'),
        ),
        default=('last_name',)
    )

    type = ListFilter(
        field_name='type',
        lookup_expr='in',
        choices=UserType.CHOICES
    )

    status = ListFilter(
        field_name='status',
        lookup_expr='in',
        choices=UserStatus.CHOICES
    )

    groups = ListFilter(
        field_name='user_groups',
        lookup_expr='in',
    )


class TenantsFilterSet(FilterSet):

    class Meta:
        model = Account
        fields = (
            'ordering',
        )

    ordering = DefaultOrderingFilter(
        fields=(
            ('tenant_name', 'tenant_name'),
            ('date_joined', 'date_joined'),
        ),
        default=('tenant_name',)
    )


class ContactsFilterSet(FilterSet):

    class Meta:
        model = Contact
        fields = (
            'ordering',
            'search',
            'source',
        )

    ordering = DefaultOrderingFilter(
        fields=(
            ('first_name', 'first_name'),
            ('last_name', 'last_name'),
            ('source', 'source'),
        ),
        default=('last_name',)
    )
    search = TsQuerySearchFilter(
        field_name='search_content',
    )
    source = ChoiceFilter(
        choices=SourceType.CHOICES
    )


class GroupsListFilterSet(FilterSet):

    class Meta:
        model = UserGroup
        fields = (
            'ordering',
        )

    ordering = DefaultOrderingFilter(
        fields=(
            ('name', 'name'),
        ),
        default=('name',)
    )
