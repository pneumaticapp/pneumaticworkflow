from django.conf import settings
from django.forms import (
    FileField,
    ModelForm,
)

from src.accounts.messages import MSG_A_0001
from src.accounts.models import (
    Contact,
)
from src.storage.services.exceptions import FileServiceException
from src.storage.services.file_service import FileServiceClient
from src.utils.logging import (
    SentryLogLevel,
    capture_sentry_message,
)


class ContactAdminForm(ModelForm):

    class Meta:
        model = Contact
        fields = (
            'first_name',
            'last_name',
            'photo_file',
            'photo',
            'job_title',
            'source',
            'email',
            'user',
            'account',
            'status',
        )

    photo_file = FileField(
        required=False,
        label='Upload photo',
    )

    def clean_photo_file(self):
        photo_file = self.cleaned_data.get('photo_file')
        if photo_file and not settings.PROJECT_CONF['STORAGE']:
            self.add_error(field='photo_file', error=MSG_A_0001)
        return photo_file

    def save(self, commit=True):

        self.instance.account = self.cleaned_data['user'].account
        photo_file = self.cleaned_data.get('photo_file', None)
        if not photo_file:
            return super().save(commit=commit)

        user = self.cleaned_data['user']
        file_service = FileServiceClient(user=user)

        try:
            file_url = file_service.upload_file_with_attachment(
                file_content=photo_file.file.getvalue(),
                filename=photo_file.name.replace(' ', '_'),
                content_type=photo_file.content_type,
                account=self.instance.account,
            )
            self.instance.photo = file_url
        except FileServiceException as ex:
            capture_sentry_message(
                message='Contact photo upload failed',
                data={
                    'filename': photo_file.name,
                    'user_id': user.id,
                    'account_id': self.instance.account.id,
                    'error': str(ex),
                },
                level=SentryLogLevel.ERROR,
            )
            self.instance.photo = None
        return super().save(commit=commit)
