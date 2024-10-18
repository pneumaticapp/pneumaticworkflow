from django.contrib import admin
from pneumatic_backend.logs.models import AccountEvent
from pneumatic_backend.logs.enums import AccountEventStatus
from pneumatic_backend.utils.dates import date_to_user_fmt


@admin.register(AccountEvent)
class AccountEventAdmin(admin.ModelAdmin):

    list_display = (
        'path',
        'method',
        'date_created_tz',
        'user_id',
        'user_name',
        'ip',
        'direction',
        'contractor',
        'colored_status',
    )

    list_filter = (
        'status',
        'event_type',
        'direction',
        'contractor',
        'method',
    )

    search_fields = (
        'path',
        'body',
    )

    fieldsets = (
        (
            None, {
                'fields': (
                    'status',
                    'date_created_tz',
                    'event_type',
                    'direction',
                    'contractor',
                )
            }
        ),
        (
            'Request', {
                'fields': (
                    'scheme',
                    'method',
                    'path',
                    'body',
                    'http_status',
                    'error'
                )
            }
        ),
        (
            'User', {
                'fields': (
                    'user',
                    'ip',
                    'auth_token',
                    'user_agent'
                )
            }
        )
    )

    readonly_fields = (
        'date_created_tz',
        'event_type',
        'http_status',
        'scheme',
        'method',
        'path',
        'user',
        'account',
        'body',
        'ip',
        'auth_token',
        'user_agent',
        'error',
        'event_type',
        'direction',
        'contractor',
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        self.user = request.user
        return qs

    def date_created_tz(self, obj):
        return date_to_user_fmt(
            date=obj.date_created,
            user=self.user
        )

    date_created_tz.short_description = 'date_created'

    def colored_status(self, obj):
        if obj.status == AccountEventStatus.SUCCESS:
            return '✔️'
        elif obj.status == AccountEventStatus.FAILED:
            return '🔴'
        return '🔵'
    colored_status.short_description = 'status'

    def user_name(self, obj):
        return obj.user.name if obj.user else 'system'

    def has_add_permission(self, request):
        return False
