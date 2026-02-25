from django import forms
from .models import Property, PropertyPhoto, Room, RoomPhoto


class PropertyForm(forms.ModelForm):
    class Meta:
        model  = Property
        fields = [
            'title', 'type', 'rent_type', 'description',
            'address', 'city', 'state', 'landmark',
            'total_floors', 'total_rooms', 'total_bedrooms',
            'total_bathrooms', 'total_kitchens', 'bathrooms_per_floor', 'area_sqft',
            'furnishing', 'has_parking', 'has_water_supply',
            'has_electricity_backup', 'has_internet', 'has_garden', 'has_balcony',
            'rent_price', 'security_deposit', 'advance_months',
            'status',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'address':     forms.Textarea(attrs={'rows': 2}),
        }

    def clean(self):
        cleaned_data = super().clean()
        rent_type  = cleaned_data.get('rent_type')
        rent_price = cleaned_data.get('rent_price')
        if rent_type == 'whole' and not rent_price:
            self.add_error('rent_price', 'Rent price is required for whole property rental.')
        return cleaned_data


PropertyPhotoFormSet = forms.inlineformset_factory(
    Property, PropertyPhoto,
    fields=['image', 'caption', 'is_cover'],
    extra=3, max_num=10, can_delete=True,
)


class RoomForm(forms.ModelForm):
    class Meta:
        model  = Room
        fields = [
            'room_number', 'room_type', 'description',
            'bedrooms', 'bathroom_type', 'kitchen_type',
            'floor_number', 'area_sqft', 'furnishing',
            'has_ac', 'has_balcony', 'wifi_included',
            'water_included', 'electricity_included',
            'rent_price', 'security_deposit', 'advance_months',
            'status',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


RoomPhotoFormSet = forms.inlineformset_factory(
    Room, RoomPhoto,
    fields=['image', 'caption', 'is_cover'],
    extra=3, max_num=10, can_delete=True,
)