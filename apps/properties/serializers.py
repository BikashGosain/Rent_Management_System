from rest_framework import serializers
from .models import Property, Room, RoomFacility, PropertyPhoto, RoomPhoto


# ── Property Photo ────────────────────────────────────────────────────────────

class PropertyPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PropertyPhoto
        fields = ['id', 'image', 'caption', 'is_cover', 'uploaded_at']


# ── Room Photo ────────────────────────────────────────────────────────────────

class RoomPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = RoomPhoto
        fields = ['id', 'image', 'caption', 'is_cover', 'uploaded_at']


# ── Room Facility ─────────────────────────────────────────────────────────────

class RoomFacilitySerializer(serializers.ModelSerializer):
    class Meta:
        model   = RoomFacility
        exclude = ['id', 'room']


# ── Room (list) — lightweight, no nested facility ─────────────────────────────

class RoomListSerializer(serializers.ModelSerializer):
    cover_photo  = serializers.SerializerMethodField()
    property_title = serializers.CharField(source='property.title', read_only=True)
    property_city  = serializers.CharField(source='property.city',  read_only=True)

    class Meta:
        model  = Room
        fields = [
            'id', 'room_number', 'room_type', 'floor_number',
            'bedrooms', 'bathroom_type', 'kitchen_type',
            'area_sqft', 'furnishing', 'rent_price',
            'security_deposit', 'advance_months', 'status',
            'property_title', 'property_city', 'cover_photo',
        ]

    def get_cover_photo(self, obj):
        cover = obj.photos.filter(is_cover=True).first() or obj.photos.first()
        if cover and cover.image:
            request = self.context.get('request')
            return request.build_absolute_uri(cover.image.url) if request else cover.image.url
        return None


# ── Room (detail) — full with facility + all photos ───────────────────────────

class RoomDetailSerializer(serializers.ModelSerializer):
    facility       = RoomFacilitySerializer(read_only=True)
    photos         = RoomPhotoSerializer(many=True, read_only=True)
    property_title = serializers.CharField(source='property.title', read_only=True)
    property_city  = serializers.CharField(source='property.city',  read_only=True)
    property_id    = serializers.IntegerField(source='property.id', read_only=True)
    owner_name     = serializers.CharField(source='property.owner.get_full_name', read_only=True)
    owner_phone    = serializers.CharField(source='property.owner.phone', read_only=True)

    class Meta:
        model  = Room
        fields = [
            'id', 'room_number', 'room_type', 'description',
            'bedrooms', 'bathroom_type', 'kitchen_type',
            'floor_number', 'area_sqft', 'furnishing',
            'rent_price', 'security_deposit', 'advance_months',
            'status', 'created_at', 'updated_at',
            'property_id', 'property_title', 'property_city',
            'owner_name', 'owner_phone',
            'facility', 'photos',
        ]


# ── Room Create/Update ────────────────────────────────────────────────────────

class RoomWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Room
        fields = [
            'room_number', 'room_type', 'description',
            'bedrooms', 'bathroom_type', 'kitchen_type',
            'floor_number', 'area_sqft', 'furnishing',
            'rent_price', 'security_deposit', 'advance_months',
            'status',
        ]

    def validate_room_number(self, value):
        # Check unique room_number inside same property
        property_id = self.context.get('property_id')
        qs = Room.objects.filter(property_id=property_id, room_number=value)
        # Exclude current instance on update
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                f'Room number "{value}" already exists in this property.'
            )
        return value


# ── Property (list) ───────────────────────────────────────────────────────────

class PropertyListSerializer(serializers.ModelSerializer):
    cover_photo      = serializers.SerializerMethodField()
    owner_name       = serializers.CharField(source='owner.get_full_name', read_only=True)
    available_rooms  = serializers.IntegerField(source='available_rooms.count', read_only=True)

    class Meta:
        model  = Property
        fields = [
            'id', 'title', 'type', 'rent_type', 'city', 'state',
            'landmark', 'furnishing', 'rent_price', 'status',
            'owner_name', 'available_rooms', 'cover_photo',
        ]

    def get_cover_photo(self, obj):
        cover = obj.photos.filter(is_cover=True).first() or obj.photos.first()
        if cover and cover.image:
            request = self.context.get('request')
            return request.build_absolute_uri(cover.image.url) if request else cover.image.url
        return None


# ── Property (detail) ─────────────────────────────────────────────────────────

class PropertyDetailSerializer(serializers.ModelSerializer):
    photos          = PropertyPhotoSerializer(many=True, read_only=True)
    rooms           = RoomListSerializer(many=True, read_only=True)
    owner_name      = serializers.CharField(source='owner.get_full_name', read_only=True)
    owner_phone     = serializers.CharField(source='owner.phone', read_only=True)
    available_rooms = serializers.IntegerField(source='available_rooms.count', read_only=True)

    class Meta:
        model  = Property
        fields = [
            'id', 'title', 'type', 'rent_type', 'description',
            'address', 'city', 'state', 'landmark',
            'total_floors', 'total_rooms', 'total_bedrooms',
            'total_bathrooms', 'total_kitchens', 'area_sqft',
            'furnishing', 'has_parking', 'has_water_supply',
            'has_electricity_backup', 'has_internet',
            'has_garden', 'has_balcony',
            'rent_price', 'security_deposit', 'advance_months',
            'status', 'created_at', 'updated_at',
            'owner_name', 'owner_phone', 'available_rooms',
            'photos', 'rooms',
        ]