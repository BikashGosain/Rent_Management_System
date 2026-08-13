from django import forms
from .models import Property, PropertyPhoto, Room, RoomPhoto, RoomFacility


class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = [
            "title",
            "type",
            "rent_type",
            "description",
            "address",
            "city",
            "state",
            "landmark",
            "total_floors",
            "total_rooms",
            "total_bedrooms",
            "total_bathrooms",
            "total_kitchens",
            "bathrooms_per_floor",
            "area_sqft",
            "furnishing",
            "has_parking",
            "has_water_supply",
            "has_electricity_backup",
            "has_internet",
            "has_garden",
            "has_balcony",
            "rent_price",
            "security_deposit",
            "advance_months",
            "status",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "address": forms.Textarea(attrs={"rows": 2}),
        }

    def clean(self):
        cleaned_data = super().clean()
        rent_type = cleaned_data.get("rent_type")
        rent_price = cleaned_data.get("rent_price")
        if rent_type == "whole" and not rent_price:
            self.add_error(
                "rent_price", "Rent price is required for whole property rental."
            )
        return cleaned_data


PropertyPhotoFormSet = forms.inlineformset_factory(
    Property,
    PropertyPhoto,
    fields=["image", "caption", "is_cover"],
    extra=3,
    max_num=10,
    can_delete=True,
)


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = [
            "room_number",
            "room_type",
            "description",
            "bedrooms",
            "bathroom_type",
            "kitchen_type",
            "floor_number",
            "area_sqft",
            "furnishing",
            "rent_price",
            "security_deposit",
            "advance_months",
            "status",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class RoomFacilityForm(forms.ModelForm):
    class Meta:
        model = RoomFacility
        exclude = ["room"]
        labels = {
            "wifi": "WiFi",
            "water_included": "Water Included",
            "electricity_included": "Electricity Included",
            "gas_included": "Gas Included",
            "ac": "AC",
            "heater": "Heater",
            "refrigerator": "Refrigerator",
            "washing_machine": "Washing Machine",
            "tv": "TV",
            "microwave": "Microwave",
            "kitchen": "Kitchen",
            "parking": "Parking",
            "balcony": "Balcony",
            "garden": "Garden",
            "storage": "Storage",
            "laundry": "Laundry",
            "security_guard": "Security Guard",
            "cctv": "CCTV",
            "lift": "Lift/Elevator",
            "housekeeping": "Housekeeping",
            "furnished": "Furnished",
            "bed": "Bed",
            "wardrobe": "Wardrobe",
            "study_table": "Study Table",
            "sofa": "Sofa",
        }


RoomPhotoFormSet = forms.inlineformset_factory(
    Room,
    RoomPhoto,
    fields=["image", "caption", "is_cover"],
    extra=3,
    max_num=10,
    can_delete=True,
)
