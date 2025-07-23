import json
from django.contrib import admin
from django.utils.safestring import mark_safe
from pneumatic_backend.logs.models import AccountEvent
from pneumatic_backend.logs.enums import AccountEventStatus
from pneumatic_backend.utils.dates import date_to_user_fmt
from pneumatic_backend.logs.filters import AccountAdminFilter
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import get_formatter_by_name


json_lexer = get_lexer_by_name('json')
formatter = get_formatter_by_name('html', style='colorful')


@admin.register(AccountEvent)
class AccountEventAdmin(admin.ModelAdmin):

    list_display = (
        'title',
        'path',
        'method',
        'date_created_tz',
        'ip',
        'direction',
        'contractor',
        'colored_status',
        'user_id',
        'user_name',
        'account',
    )

    list_filter = (
        'status',
        'event_type',
        'direction',
        'contractor',
        'method',
        AccountAdminFilter,
    )

    search_fields = (
        'title',
        'path',
    )

    fieldsets = (
        (
            None, {
                'fields': (
                    'title',
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
                    'formatted_request_data',
                    'http_status',
                    'formatted_response_data'
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
        'title',
        'date_created_tz',
        'event_type',
        'http_status',
        'scheme',
        'method',
        'path',
        'user',
        'account',
        'formatted_request_data',
        'ip',
        'auth_token',
        'user_agent',
        'formatted_response_data',
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

    def formatted_request_data(self, instance):
        if instance.request_data:
            response = json.dumps(
                instance.request_data,
                sort_keys=True,
                indent=2,
                ensure_ascii=False
            )
            response = highlight(response, json_lexer, formatter)
            style = "<style>" + formatter.get_style_defs() + "</style><br>"
            return mark_safe(style + response)
        else:
            return '-'
    formatted_request_data.short_description = 'request_data'

    def formatted_response_data(self, instance):
        if instance.response_data:
            response = json.dumps(
                instance.response_data,
                sort_keys=True,
                indent=2,
                ensure_ascii=False
            )
            response = highlight(response, json_lexer, formatter)
            style = "<style>" + formatter.get_style_defs() + "</style><br>"
            return mark_safe(style + response)
        else:
            return '-'
    formatted_response_data.short_description = 'response_data'
