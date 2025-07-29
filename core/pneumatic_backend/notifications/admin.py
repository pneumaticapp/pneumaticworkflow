from django.contrib import admin
from django.contrib.admin import ModelAdmin

from pneumatic_backend.notifications.models import Device


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
