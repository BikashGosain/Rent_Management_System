from django import forms
from .models import Agreement


# Default terms template
DEFAULT_TERMS = """1. The tenant agrees to pay rent on or before the 5th of every month.
2. The tenant shall not sublet the property without written consent from the owner.
3. The tenant shall maintain the property in good condition.
4. The tenant shall not cause any disturbance to neighbors.
5. Any damage to the property beyond normal wear and tear shall be charged to the tenant.
6. The tenant must give 30 days notice before vacating the property.
7. The security deposit will be refunded within 30 days of vacating, after deducting any dues.
8. The owner reserves the right to inspect the property with prior notice.
9. This agreement is governed by the laws of Nepal."""


class AgreementForm(forms.ModelForm):
    class Meta:
        model  = Agreement
        fields = [
            'start_date', 'end_date',
            'rent_amount', 'security_deposit', 'advance_amount',
            'notice_period_days', 'terms_conditions', 'document',
        ]
        widgets = {
            'start_date':       forms.DateInput(attrs={'type': 'date'}),
            'end_date':         forms.DateInput(attrs={'type': 'date'}),
            'terms_conditions': forms.Textarea(attrs={'rows': 10}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['terms_conditions'].initial = DEFAULT_TERMS

    def clean(self):
        cleaned_data = super().clean()
        start_date   = cleaned_data.get('start_date')
        end_date     = cleaned_data.get('end_date')
        if start_date and end_date:
            if end_date <= start_date:
                self.add_error('end_date', 'End date must be after start date.')
        return cleaned_data