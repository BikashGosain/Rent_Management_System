from django import forms
from .models import Agreement

DEFAULT_TERMS = """1. Rent is due on the 5th of every month.
2. A late fee applies after 7 days of non-payment.
3. Tenant must maintain the property in good condition.
4. No unauthorized alterations to the property.
5. Tenant is responsible for minor repairs under Rs. 500.
6. Subletting is not allowed without owner's written consent.
7. Owner must give proper notice before entering the property.
8. Tenant must give notice as per agreement before vacating.
9. Security deposit will be refunded within 30 days of vacating."""


class AgreementForm(forms.ModelForm):
    class Meta:
        model  = Agreement
        fields = [
            'rental_type', 'short_term_unit', 'short_term_duration',
            'start_date', 'end_date',
            'rent_amount', 'security_deposit', 'advance_amount',
            'notice_period_days', 'terms_conditions', 'document',
            'auto_renew',
        ]
        widgets = {
            'start_date':        forms.DateInput(attrs={'type': 'date'}),
            'end_date':          forms.DateInput(attrs={'type': 'date'}),
            'terms_conditions':  forms.Textarea(attrs={'rows': 6}),
            'notice_period_days': forms.NumberInput(attrs={'min': 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['terms_conditions'].initial = DEFAULT_TERMS

    def clean(self):
        cleaned = super().clean()
        rental_type = cleaned.get('rental_type')
        start_date  = cleaned.get('start_date')
        end_date    = cleaned.get('end_date')

        if rental_type == 'fixed':
            if not end_date:
                raise forms.ValidationError('End date is required for fixed term rental.')
            if end_date and start_date and end_date <= start_date:
                raise forms.ValidationError('End date must be after start date.')

        if rental_type == 'short':
            if not cleaned.get('short_term_unit'):
                raise forms.ValidationError('Please select daily or weekly for short term rental.')
            if not cleaned.get('short_term_duration'):
                raise forms.ValidationError('Please enter duration for short term rental.')

        return cleaned


class NoticeForm(forms.ModelForm):
    class Meta:
        model  = Agreement
        fields = ['notice_type', 'notice_vacate_date', 'notice_reason']
        widgets = {
            'notice_vacate_date': forms.DateInput(attrs={'type': 'date'}),
            'notice_reason':      forms.Textarea(attrs={'rows': 3, 'placeholder': 'Explain your reason...'}),
        }
        labels = {
            'notice_type':        'Type of Notice',
            'notice_vacate_date': 'Expected Vacate Date',
            'notice_reason':      'Reason',
        }


class NoticeResponseForm(forms.ModelForm):
    class Meta:
        model  = Agreement
        fields = ['notice_status', 'notice_response']
        widgets = {
            'notice_response': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Your response to the notice...'}),
        }
        labels = {
            'notice_status':   'Decision',
            'notice_response': 'Response Message',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['notice_status'].choices = [
            ('approved', 'Approve Notice'),
            ('rejected', 'Reject Notice'),
            ('mutual',   'Agree Mutually'),
        ]

class ExtensionRequestForm(forms.ModelForm):
    class Meta:
        model  = Agreement
        fields = ['extension_duration', 'extension_unit', 'extension_reason']
        widgets = {
            'extension_reason': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Why do you want to extend your stay?'
            }),
            'extension_duration': forms.NumberInput(attrs={'min': 1}),
        }
        labels = {
            'extension_duration': 'Extend by (number)',
            'extension_unit':     'Unit',
            'extension_reason':   'Reason for Extension',
        }


class ExtensionResponseForm(forms.ModelForm):
    class Meta:
        model  = Agreement
        fields = ['extension_status', 'extension_response']
        widgets = {
            'extension_response': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Your response...'
            }),
        }
        labels = {
            'extension_status':   'Decision',
            'extension_response': 'Response Message',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['extension_status'].choices = [
            ('approved', 'Approve Extension'),
            ('rejected', 'Reject Extension'),
        ]