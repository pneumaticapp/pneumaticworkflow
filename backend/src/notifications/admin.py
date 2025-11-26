from django.contrib import admin

from src.notifications.models import EmailTemplateModel


@admin.register(EmailTemplateModel)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = (
        'account',
        'template_type',
        'subject',
        'is_active',
        'updated_at',
    )
    list_filter = (
        'template_type',
        'is_active',
        'account',
    )
    search_fields = (
        'account__name',
        'subject',
        'template_type',
    )
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': ('account', 'template_type', 'is_active'),
        }),
        ('Content', {
            'fields': ('subject', 'content'),
            'description': 'Use {{variable_name}} for variables',
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
