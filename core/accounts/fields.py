from django.db import models
from django import forms


class LowerField(models.Field):
    def to_python(self, value):
        value = super().to_python(value)
        if value is not None:
            value = value.lower()
        return value


class EmailLowerField(LowerField, models.EmailField):
    pass


class CharLowerField(LowerField, models.CharField):
    pass


class FormTruncatingCharField(forms.CharField):
    def clean(self, value):
        value = self.to_python(value)

        if value is None:
            return value

        value = value[:self.max_length]
        self.validate(value)
        self.run_validators(value)

        return value


class TruncatingCharField(models.CharField):
    def formfield(self, **kwargs):
        defaults = {'form_class': FormTruncatingCharField}
        defaults.update(kwargs)
        return super(TruncatingCharField, self).formfield(**defaults)

    def get_prep_value(self, value):
        value = super(TruncatingCharField, self).get_prep_value(value)
        if value:
            return value[:self.max_length]
        return value
