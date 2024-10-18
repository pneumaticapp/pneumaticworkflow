from django.contrib import admin
from django.contrib.admin import (
    ModelAdmin,
    StackedInline
)
from pneumatic_backend.ai.models import (
    OpenAiPrompt,
    OpenAiMessage
)
from django.forms.models import BaseInlineFormSet
from django.forms import ModelForm, ValidationError


class OpenAiMessageFormset(BaseInlineFormSet):

    def clean(self):
        deleted_forms = 0
        deactivated_forms = 0
        for form in self.forms:
            try:
                if form.cleaned_data:
                    if form.cleaned_data['DELETE']:
                        deleted_forms += 1
                    if not form.cleaned_data['is_active']:
                        deactivated_forms += 1

            except AttributeError:
                pass

        if len(self.forms) == deleted_forms:
            raise ValidationError('At least one message required')
        if len(self.forms) == deactivated_forms:
            raise ValidationError('At least one active message required')


class OpenAiPromptForm(ModelForm):

    def clean(self):
        super().clean()
        is_active = self.cleaned_data['is_active']
        if not is_active and self.instance.id:
            target = self.cleaned_data['target']
            if OpenAiPrompt.objects.active().by_target(target).filter(
                id=self.instance.id
            ).count() == 1:
                raise ValidationError(
                    'You cannot deactivate the last active prompt for a target'
                )


class OpenAiMessageItemInline(StackedInline):

    model = OpenAiMessage
    extra = 0
    min_num = 1
    formset = OpenAiMessageFormset


@admin.register(OpenAiPrompt)
class OpenAiPromptAdmin(ModelAdmin):

    model = OpenAiPrompt
    inlines = (OpenAiMessageItemInline,)
    form = OpenAiPromptForm
    list_display = (
        '__str__',
        'comment',
        'target',
        'date_changed',
        'is_active',
    )

    def has_delete_permission(self, request, obj=None):
        result = super().has_delete_permission(request, obj)
        if obj and obj.is_active and OpenAiPrompt.objects.active().by_target(
            obj.target
        ).count() == 1:
            result = False
        return result

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.is_active:
            OpenAiPrompt.objects.active().by_target(obj.target).exclude(
                id=obj.id
            ).update(is_active=False)
