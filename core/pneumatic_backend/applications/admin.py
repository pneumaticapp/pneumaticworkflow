import os
from django.conf import settings
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.forms import ModelForm, forms, CharField
from django.utils.safestring import mark_safe
from tinymce.widgets import TinyMCE

from pneumatic_backend.applications.models import Integration
from pneumatic_backend.storage.google_cloud import GoogleCloudService
from pneumatic_backend.processes.messages.workflow import MSG_PW_0001


class IntegrationCreateForm(ModelForm):

    class Meta:
        model = Integration
        fields = (
            'name',
            'image_file',
            'short_description',
            'long_description',
            'button_text',
            'url',
            'order',
        )

    image_file = forms.FileField(
        required=False,
        help_text='Logo of service we integrated with. '
                  'Only svg files are supported!'
    )
    long_description = CharField(
        widget=TinyMCE(),
        help_text='Long description to be displayed on the integration page.'
    )

    def clean(self):
        cleaned_data = super(IntegrationCreateForm, self).clean()
        cleaned_file = cleaned_data.get("image_file")
        if cleaned_file:
            if os.path.splitext(cleaned_file.name)[1].lower() != '.svg':
                self.add_error('image_file', 'SVG image required')
        return cleaned_data

    def clean_image_file(self):
        image_file = self.cleaned_data.get('image_file')
        if image_file and not settings.PROJECT_CONF['STORAGE']:
            self.add_error(field='image_file', error=MSG_PW_0001)
        return image_file

    def save(self, commit=True):

        image = self.cleaned_data.get('image_file', None)
        if not image:
            return super(IntegrationCreateForm, self).save(commit=commit)

        file_path = image.name.replace(' ', '_')
        storage = GoogleCloudService()
        public_url = storage.upload_from_binary(
            filepath=file_path,
            binary=image.file.getvalue(),
            content_type='image/svg+xml'
        )
        integration = super(IntegrationCreateForm, self).save(commit=commit)
        integration.logo = public_url
        integration.save()
        return integration


class IntegrationAdmin(ModelAdmin):
    form = IntegrationCreateForm

    def logo_preview(self, obj):
        return mark_safe(
            f'<image src={obj.logo} style="max-width: 200px;">'
        )

    readonly_fields = ['id', 'logo_preview']

    list_display = ('name', 'short_description', 'is_active')
    fieldsets = (
        (None, {
            'fields': (
                'id',
                'name',
                'image_file',
                'short_description',
                'long_description',
                'button_text',
                'url',
                'order',
                'is_active',
                'logo_preview',
            ),
        }),
    )


admin.site.register(Integration, IntegrationAdmin)
