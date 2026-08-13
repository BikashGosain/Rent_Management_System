from django import forms
from .models import Booking


class BookingRequestForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["move_in_date", "move_out_date", "message"]
        widgets = {
            "move_in_date": forms.DateInput(attrs={"type": "date"}),
            "move_out_date": forms.DateInput(attrs={"type": "date"}),
            "message": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Optional message to the owner..."}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        move_in_date = cleaned_data.get("move_in_date")
        move_out_date = cleaned_data.get("move_out_date")
        if move_in_date and move_out_date:
            if move_out_date <= move_in_date:
                self.add_error(
                    "move_out_date", "Move out date must be after move in date."
                )
        return cleaned_data


class OwnerResponseForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["owner_note"]
        widgets = {
            "owner_note": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Optional note to tenant..."}
            ),
        }
