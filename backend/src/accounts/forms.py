from django.conf import settings
from django.forms import (
    FileField,
    ModelForm,
)

from src.accounts.messages import MSG_A_0001
from src.accounts.models import (
    Contact,
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
        label='Upload photo to Google drive',
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

        # TODO: Integrate with file service microservice
        self.instance.photo = None
        return super().save(commit=commit)
