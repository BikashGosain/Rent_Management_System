from rest_framework import serializers
from .models import Property, Room, RoomFacility, PropertyPhoto, RoomPhoto

class PropertyPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PropertyPhoto
        fields = ['id', 'image', 'caption', 'is_cover']

class RoomFacilitySerializer(serializers.ModelSerializer):
    class Meta:
        model  = RoomFacility
        exclude = ['id', 'room']

class RoomSerializer(serializers.ModelSerializer):
    facility = RoomFacilitySerializer(read_only=True)
    photos   = PropertyPhotoSerializer(many=True, read_only=True)

    class Meta:
        model  = Room
        fields = [
            'id', 'room_number', 'room_type', 'description',
            'bedrooms', 'bathroom_type', 'kitchen_type',
            'floor_number', 'area_sqft', 'furnishing',
            'rent_price', 'security_deposit', 'status',
            'facility', 'photos',
        ]

class PropertySerializer(serializers.ModelSerializer):
    photos = PropertyPhotoSerializer(many=True, read_only=True)
    rooms  = RoomSerializer(many=True, read_only=True)
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)

    class Meta:
        model  = Property
        fields = [
            'id', 'title', 'type', 'rent_type', 'description',
            'address', 'city', 'state', 'landmark',
            'total_floors', 'total_rooms', 'area_sqft',
            'furnishing', 'has_parking', 'has_water_supply',
            'has_internet', 'has_electricity_backup',
            'rent_price', 'security_deposit', 'status',
            'owner_name', 'photos', 'rooms', 'created_at',
        ]