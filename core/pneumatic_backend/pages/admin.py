from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.forms import ModelForm
from django.forms.fields import CharField
from django.forms.widgets import Textarea
from pneumatic_backend.pages.models import Page


class PageAdminForm(ModelForm):

    class Meta:
        fields = (
            'slug',
            'title',
            'description'
        )
    title = CharField(widget=Textarea)


@admin.register(Page)
class PageAdmin(ModelAdmin):

    form = PageAdminForm
    model = Page
