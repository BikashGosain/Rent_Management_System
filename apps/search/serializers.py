# apps/search/serializers.py
from rest_framework import serializers
from apps.properties.models import Property, Room


class SearchPropertySerializer(serializers.ModelSerializer):
    cover_photo = serializers.SerializerMethodField()
    owner_name = serializers.CharField(source="owner.get_full_name", read_only=True)
    owner_phone = serializers.CharField(source="owner.phone", read_only=True)
    available_rooms = serializers.IntegerField(
        source="available_rooms.count", read_only=True
    )
    target_type = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            "id",
            "title",
            "type",
            "rent_type",
            "description",
            "address",
            "city",
            "state",
            "landmark",
            "total_bedrooms",
            "total_bathrooms",
            "area_sqft",
            "furnishing",
            "has_parking",
            "has_internet",
            "has_water_supply",
            "has_electricity_backup",
            "has_garden",
            "has_balcony",
            "rent_price",
            "security_deposit",
            "advance_months",
            "status",
            "available_rooms",
            "owner_name",
            "owner_phone",
            "cover_photo",
            "target_type",
        ]

    def get_cover_photo(self, obj):
        cover = obj.photos.filter(is_cover=True).first() or obj.photos.first()
        if cover and cover.image:
            request = self.context.get("request")
            return (
                request.build_absolute_uri(cover.image.url)
                if request
                else cover.image.url
            )
        return None

    def get_target_type(self, obj):
        return "whole_property" if obj.rent_type == "whole" else "room_property"


class SearchRoomSerializer(serializers.ModelSerializer):
    cover_photo = serializers.SerializerMethodField()
    property_title = serializers.CharField(source="property.title", read_only=True)
    property_city = serializers.CharField(source="property.city", read_only=True)
    property_type = serializers.CharField(source="property.type", read_only=True)
    property_address = serializers.CharField(source="property.address", read_only=True)
    property_landmark = serializers.CharField(
        source="property.landmark", read_only=True
    )
    owner_name = serializers.CharField(
        source="property.owner.get_full_name", read_only=True
    )
    owner_phone = serializers.CharField(source="property.owner.phone", read_only=True)
    target_type = serializers.SerializerMethodField()

    # Facilities (flattened for easy use)
    wifi = serializers.BooleanField(
        source="facility.wifi", read_only=True, default=False
    )
    ac = serializers.BooleanField(source="facility.ac", read_only=True, default=False)
    parking = serializers.BooleanField(
        source="facility.parking", read_only=True, default=False
    )
    laundry = serializers.BooleanField(
        source="facility.laundry", read_only=True, default=False
    )
    lift = serializers.BooleanField(
        source="facility.lift", read_only=True, default=False
    )
    cctv = serializers.BooleanField(
        source="facility.cctv", read_only=True, default=False
    )
    water_included = serializers.BooleanField(
        source="facility.water_included", read_only=True, default=False
    )

    class Meta:
        model = Room
        fields = [
            "id",
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
            "target_type",
            "property_title",
            "property_city",
            "property_type",
            "property_address",
            "property_landmark",
            "owner_name",
            "owner_phone",
            "wifi",
            "ac",
            "parking",
            "laundry",
            "lift",
            "cctv",
            "water_included",
            "cover_photo",
        ]

    def get_cover_photo(self, obj):
        cover = obj.photos.filter(is_cover=True).first() or obj.photos.first()
        if cover and cover.image:
            request = self.context.get("request")
            return (
                request.build_absolute_uri(cover.image.url)
                if request
                else cover.image.url
            )
        return None

    def get_target_type(self, obj):
        return "room"
