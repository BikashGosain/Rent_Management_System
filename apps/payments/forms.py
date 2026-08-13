from django import forms
from .models import Payment


class PaymentCreateForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = [
            "payment_type",
            "payment_method",
            "amount",
            "due_date",
            "month",
            "year",
            "notes",
        ]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }


class PaymentMarkPaidForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["payment_method", "paid_date", "transaction_id", "receipt", "notes"]
        widgets = {
            "paid_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }
