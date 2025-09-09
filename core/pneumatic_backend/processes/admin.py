from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.postgres import fields as pg_fields
from django_json_widget.widgets import JSONEditorWidget
from pneumatic_backend.processes.models import (
    SystemTemplate,
    SystemWorkflowKickoffData,
    SystemTemplateCategory,
)


@admin.register(SystemTemplateCategory)
class SystemTemplateCategoryAdmin(ModelAdmin):

    list_display = ('name', 'order', 'color', 'is_active',)
    exclude = ('is_deleted',)


@admin.register(SystemTemplate)
class SystemTemplateAdmin(ModelAdmin):
    fieldsets = (
        (None, {
            'fields': (
                'is_active',
                'name',
                'description',
                'type',
                'category',
                'template',
            ),
        }),
    )
    list_display = ('name', 'type', 'category', 'is_active',)
    list_filter = ('type', 'category', 'is_active')

    formfield_overrides = {
        pg_fields.JSONField: {
            'widget': JSONEditorWidget
        },
    }


@admin.register(SystemWorkflowKickoffData)
class SystemWorkflowKickoffDataAdmin(ModelAdmin):

    fields = (
        'is_active',
        'order',
        'name',
        'system_template',
        'user_role',
        'kickoff_data',
    )

    list_display = ('name', 'user_role', 'is_active', 'order')
    list_filter = ('user_role', 'is_active')
    list_editable = ('order', 'is_active')

    formfield_overrides = {
        pg_fields.JSONField: {
            'widget': JSONEditorWidget
        }
    }
