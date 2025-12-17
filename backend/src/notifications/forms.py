from django import forms

from src.notifications.enums import EmailType
from src.notifications.models import EmailTemplateModel


class EmailTemplateAdminForm(forms.ModelForm):
    """Custom form for EmailTemplate admin with multiple select."""

    email_types = forms.MultipleChoiceField(
        choices=EmailType.CHOICES,
        widget=forms.CheckboxSelectMultiple,
        help_text='Select email types that will use this template',
    )

    class Meta:
        model = EmailTemplateModel
        fields = [
            'account',
            'name',
            'email_types',
            'subject',
            'content',
            'is_active',
        ]
        widgets = {
            'content': forms.Textarea(attrs={'rows': 20, 'cols': 80}),
            'subject': forms.TextInput(attrs={'size': 80}),
        }
