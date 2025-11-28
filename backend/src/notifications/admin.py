from django import forms
from django.contrib import admin
from django.contrib.admin import ModelAdmin

from src.notifications.enums import EmailTemplate
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


class EmailTemplateAdminForm(forms.ModelForm):
    """Custom form for EmailTemplate admin with multiple select."""

    template_types = forms.MultipleChoiceField(
        choices=[
            (choice, choice) for choice in EmailTemplate.LITERALS.__args__
        ],
        widget=forms.CheckboxSelectMultiple,
        help_text='Select email types that will use this template',
    )

    class Meta:
        model = EmailTemplateModel
        fields = [
            'account',
            'name',
            'template_types',
            'subject',
            'content',
            'is_active',
        ]
        widgets = {
            'content': forms.Textarea(attrs={'rows': 20, 'cols': 80}),
            'subject': forms.TextInput(attrs={'size': 80}),
        }


@admin.register(EmailTemplateModel)
class EmailTemplateAdmin(admin.ModelAdmin):
    form = EmailTemplateAdminForm

    list_display = (
        'account',
        'name',
        'get_template_types_display',
        'subject',
        'is_active',
    )
    list_filter = (
        'template_types',
        'is_active',
        'account',
    )
    search_fields = (
        'account__name',
        'name',
        'subject',
        'template_types',
    )
    readonly_fields = ()

    fieldsets = (
        (None, {
            'fields': ('account', 'name', 'template_types', 'is_active'),
        }),
        ('Content', {
            'fields': ('subject', 'content'),
            'description': (
                'Use {{variable_name}} for variables. '
                'Available variables depend on email type.'
            ),
        }),
    )

    def get_template_types_display(self, obj):
        """Display template types in list view."""
        return obj.get_template_types_display()
    get_template_types_display.short_description = 'Template Types'
