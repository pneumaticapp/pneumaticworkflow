from django.contrib import admin
from django.contrib.admin import ModelAdmin
from pneumatic_backend.faq.models import FaqItem


@admin.register(FaqItem)
class FaqItemAdmin(ModelAdmin):

    model = FaqItem
    list_display = (
        'question',
        'is_active',
        'order',
    )
    list_editable = (
        'order',
        'is_active',
    )
    exclude = (
        'is_deleted',
    )
    list_filter = (
        'is_active',
    )
