from django.forms import (
    ModelForm,
    FileField,
)
from django.conf import settings
from pneumatic_backend.accounts.models import (
    Contact
)
from pneumatic_backend.storage.google_cloud import (
    GoogleCloudService
)
from pneumatic_backend.accounts.messages import MSG_A_0001


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
        label='Upload photo to Google drive'
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

        file_path = photo_file.name.replace(' ', '_')
        storage = GoogleCloudService()
        public_url = storage.upload_from_binary(
            filepath=file_path,
            binary=photo_file.file.getvalue(),
            content_type=photo_file.content_type
        )
        self.instance.photo = public_url
        return super().save(commit=commit)
