from django.contrib import admin
from django.contrib.admin import ModelAdmin

from src.notifications.forms import EmailTemplateAdminForm
from src.notifications.models import Device, EmailTemplateModel


@admin.register(Device)
class DeviceAdmin(ModelAdmin):
    list_filter = ('is_active',)
    list_display = (
        'user',
        'is_app',
        'is_active',
        'date_created',
        'description',
    )
    search_fields = (
        'user__first_name',
        'user__last_name',
        'user__email',
        'description',
    )
    readonly_fields = (
        'user',
        'is_app',
        'description',
        'date_created',
        'date_updated',
        'token',
    )
    fields = (
        'is_active',
        'is_app',
        'user',
        'description',
        'date_created',
        'date_updated',
        'token',
    )

    def has_add_permission(self, obj):
        return False


@admin.register(EmailTemplateModel)
class EmailTemplateAdmin(admin.ModelAdmin):
    form = EmailTemplateAdminForm

    list_display = (
        'account',
        'name',
        'get_email_types_display',
        'subject',
        'is_active',
    )
    list_filter = (
        'email_types',
        'is_active',
        'account',
    )
    search_fields = (
        'account__name',
        'name',
        'subject',
        'email_types',
    )
    list_editable = ('is_active',)
    list_per_page = 25

    fieldsets = (
        (None, {
            'fields': ('account', 'name', 'email_types', 'is_active'),
        }),
        ('Content', {
            'fields': ('subject', 'content'),
            'description': (
                'Templates support Django template syntax with '
                '{{variable_name}}.\n\n'
                'STANDARD VARIABLES (available in all templates):\n'
                '  {{backend_url}}, {{frontend_url}}, {{logo_lg}}, '
                '{{logo_sm}}, {{date}}, {{year}}\n\n'
                'AUTH TEMPLATES (Reset password, Verification, Transfer, '
                'Deactivated):\n'
                '  {{title}} - email title\n'
                '  {{content}} - email content (HTML)\n'
                '  {{button_text}} - button text\n'
                '  {{link}} - action link (full URL)\n'
                '  {{token}} - security token\n'
                '  {{first_name}}, {{sender_name}}, {{company_name}}\n\n'
                'TASK TEMPLATES (New, Returned, Overdue, Mention):\n'
                '  {{title}} - email title\n'
                '  {{template}} - workflow template name\n'
                '  {{workflow_name}}, {{task_name}}, {{task_id}}\n'
                '  {{task_description}} - HTML content\n'
                '  {{task_link}} - link to task (full URL)\n'
                '  {{due_in}}, {{overdue}} - formatted time\n'
                '  {{started_by}} - {name, avatar} dict\n'
                '  {{unsubscribe_link}} - full URL\n'
                '  {{user_first_name}}\n\n'
                'DIGEST TEMPLATES (Workflows, Tasks, Notifications):\n'
                '  {{title}} - digest title\n'
                '  {{date_from}}, {{date_to}} - formatted dates\n'
                '  {{workflows_link}}, {{tasks_link}}, '
                '{{notifications_link}} - full URLs\n'
                '  {{unsubscribe_link}} - full URL\n'
                '  + custom digest data from context\n'
            ),
        }),
    )

    def get_email_types_display(self, obj):
        """Display email types in list view."""
        return obj.get_email_types_display()
    get_email_types_display.short_description = 'Email Types'

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('account')
