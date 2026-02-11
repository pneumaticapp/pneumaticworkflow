import os

from django.conf import settings
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.forms import CharField, ModelForm, forms
from django.utils.safestring import mark_safe
from tinymce.widgets import TinyMCE

from src.applications.models import Integration
from src.processes.messages.workflow import MSG_PW_0001
from src.storage.services.exceptions import (
    FileServiceConnectionException,
    FileServiceException,
)
from src.storage.services.file_service import FileServiceClient
from src.utils.logging import (
    SentryLogLevel,
    capture_sentry_message,
)


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
                  'Only svg files are supported!',
    )
    long_description = CharField(
        widget=TinyMCE(),
        help_text='Long description to be displayed on the integration page.',
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        cleaned_file = cleaned_data.get("image_file")
        if (
            cleaned_file
            and os.path.splitext(cleaned_file.name)[1].lower() != '.svg'
        ):
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
            return super().save(commit=commit)

        file_url = None
        try:
            file_service = FileServiceClient(user=self.user)
            file_url = file_service.upload_file_with_attachment(
                file_content=image.read(),
                filename=image.name.replace(' ', '_'),
                content_type='image/svg+xml',
                account=self.user.account,
            )
        except (
            FileServiceConnectionException,
            FileServiceException,
        ) as ex:
            capture_sentry_message(
                message='Integration logo upload failed',
                data={
                    'filename': image.name,
                    'user_id': self.user.id,
                    'error': str(ex),
                },
                level=SentryLogLevel.ERROR,
            )

        integration = super().save(commit=commit)
        if file_url is not None:
            integration.logo = file_url
            integration.save(update_fields=['logo'])
        return integration


class IntegrationAdmin(ModelAdmin):
    form = IntegrationCreateForm

    def get_form(self, request, obj=None, **kwargs):
        form_class = super().get_form(request, obj, **kwargs)

        class IntegrationFormWithUser(form_class):
            def __init__(self, *args, **kwargs):
                kwargs['user'] = request.user
                super().__init__(*args, **kwargs)

        return IntegrationFormWithUser

    def logo_preview(self, obj):
        return mark_safe(
            f'<image src={obj.logo} style="max-width: 200px;">',
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
