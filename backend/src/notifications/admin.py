from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.utils.safestring import mark_safe

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
            'description': mark_safe(
                '<div style="margin-bottom: 10px;">'
                'Templates support Django template syntax with '
                '<code>{{variable_name}}</code>.</div>'
                '<div style="margin-bottom: 10px;"><strong>STANDARD '
                'VARIABLES:</strong><br>'
                '&nbsp;&nbsp;<code>{{logo_lg}}</code> - company logo URL<br>'
                '&nbsp;&nbsp;Use <code>{% now "Y" %}</code> for current year, '
                '<code>{% now "d M, Y" %}</code> for current date<br>'
                '&nbsp;&nbsp;All URLs are provided as complete links</div>'
                '<div style="margin-bottom: 10px;">'
                '<strong>AUTH TEMPLATES</strong> '
                '(Reset password, Verification, Transfer, Deactivated):<br>'
                '&nbsp;&nbsp;<code>{{title}}</code> - email title<br>'
                '&nbsp;&nbsp;<code>{{content}}</code> - '
                'email content (HTML)<br>'
                '&nbsp;&nbsp;<code>{{additional_content}}</code> - '
                'additional content (HTML)<br>'
                '&nbsp;&nbsp;<code>{{button_text}}</code> - button text<br>'
                '&nbsp;&nbsp;<code>{{link}}</code> - '
                'action link (full URL)<br>'
                '&nbsp;&nbsp;<code>{{reset_link}}</code> - '
                'password reset link<br>'
                '&nbsp;&nbsp;<code>{{verification_link}}</code> - '
                'email verification link<br>'
                '&nbsp;&nbsp;<code>{{transfer_link}}</code> - '
                'user transfer link<br>'
                '&nbsp;&nbsp;<code>{{support_link}}</code> - '
                'support page link<br>'
                '&nbsp;&nbsp;<code>{{token}}</code> - security token<br>'
                '&nbsp;&nbsp;<code>{{first_name}}</code> - '
                'user first name (verification only)<br>'
                '&nbsp;&nbsp;<code>{{sender_name}}</code> - '
                'inviter name (transfer only)<br>'
                '&nbsp;&nbsp;<code>{{company_name}}</code> - '
                'company name (transfer only)<br>'
                '&nbsp;&nbsp;<code>{{image_url}}</code> - '
                'image URL (deactivated user only)</div>'
                '<div style="margin-bottom: 10px;">'
                '<strong>TASK TEMPLATES</strong> '
                '(New, Returned, Overdue, Guest New, Mention):<br>'
                '&nbsp;&nbsp;<code>{{title}}</code> - email title<br>'
                '&nbsp;&nbsp;<code>{{template}}</code> - '
                'workflow template name<br>'
                '&nbsp;&nbsp;<code>{{workflow_name}}</code>, '
                '<code>{{workflow_id}}</code> - workflow info<br>'
                '&nbsp;&nbsp;<code>{{task_name}}</code>, '
                '<code>{{task_id}}</code> - task info<br>'
                '&nbsp;&nbsp;<code>{{task_description}}</code> - '
                'HTML content<br>'
                '&nbsp;&nbsp;<code>{{task_link}}</code>, '
                '<code>{{link}}</code> - link to task (full URL)<br>'
                '&nbsp;&nbsp;<code>{{due_in}}</code>, '
                '<code>{{overdue}}</code> - formatted time<br>'
                '&nbsp;&nbsp;<code>{{started_by}}</code> - '
                'object with name and avatar fields<br>'
                '&nbsp;&nbsp;<code>{{unsubscribe_token}}</code>, '
                '<code>{{unsubscribe_link}}</code> - unsubscribe data<br>'
                '&nbsp;&nbsp;<code>{{user_first_name}}</code> - '
                'assignee name<br>'
                '&nbsp;&nbsp;<code>{{guest_sender_name}}</code> - '
                'sender name for guest tasks<br>'
                '&nbsp;&nbsp;<code>{{workflow_starter_*}}</code> - '
                'workflow starter info (overdue only)<br>'
                '&nbsp;&nbsp;<code>{{user_type}}</code>, '
                '<code>{{token}}</code> - guest access data</div>'
                '<div style="margin-bottom: 10px;">'
                '<strong>DIGEST TEMPLATES</strong> '
                '(Workflows, Tasks):<br>'
                '&nbsp;&nbsp;<code>{{title}}</code> - digest title<br>'
                '&nbsp;&nbsp;<code>{{date_from}}</code>, '
                '<code>{{date_to}}</code> - formatted dates<br>'
                '&nbsp;&nbsp;<code>{{workflows_link}}</code>, '
                '<code>{{tasks_link}}</code>, '
                '<code>{{notifications_link}}</code> - full URLs<br>'
                '&nbsp;&nbsp;<code>{{base_link}}</code> - '
                'base URL for links<br>'
                '&nbsp;&nbsp;<code>{{unsubscribe_token}}</code>, '
                '<code>{{unsubscribe_link}}</code> - unsubscribe data<br>'
                '&nbsp;&nbsp;<code>{{user_first_name}}</code> - user name<br>'
                '&nbsp;&nbsp;<code>{{status_labels}}</code> - '
                'status labels object<br>'
                '&nbsp;&nbsp;<code>{{status_queries}}</code> - '
                'query parameters object<br>'
                '&nbsp;&nbsp;<code>{{template_query_param}}</code> - '
                'template filter param<br>'
                '&nbsp;&nbsp;<code>{{templates}}</code> - '
                'array of template objects<br>'
                '&nbsp;&nbsp;<code>{{is_tasks_digest}}</code> - '
                'digest type flag<br>'
                '&nbsp;&nbsp;<code>{{started}}</code>, '
                '<code>{{in_progress}}</code>, '
                '<code>{{overdue}}</code>, <code>{{completed}}</code> - '
                'counters<br>&nbsp;&nbsp;+ '
                'custom digest data from context</div>',
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
