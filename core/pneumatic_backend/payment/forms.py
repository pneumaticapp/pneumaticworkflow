from django import forms
from pneumatic_backend.payment.models import Price


class PriceInlineForm(forms.ModelForm):

    class Meta:
        model = Price
        fields = '__all__'

    def clean_min_quantity(self):
        min_quantity = self.cleaned_data.get('min_quantity')
        max_quantity = self.cleaned_data.get('max_quantity')
        if min_quantity >= max_quantity:
            self.add_error(
                field='min_quantity',
                error='value must be less then the "max_quantity" value'
            )
        return min_quantity

    def clean_max_quantity(self):
        max_quantity = self.cleaned_data.get('max_quantity')
        if max_quantity > 10000:
            self.add_error(
                field='max_quantity',
                error='value must be less than or equal to 10000'
            )
        return max_quantity
