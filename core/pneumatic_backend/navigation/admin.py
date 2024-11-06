from django.contrib import admin
from django.contrib.admin import (
    ModelAdmin,
    StackedInline
)
from pneumatic_backend.navigation.models import Menu, MenuItem


class MenuItemInline(StackedInline):

    model = MenuItem
    extra = 0


@admin.register(Menu)
class MenuAdmin(ModelAdmin):

    model = Menu
    inlines = (MenuItemInline,)
