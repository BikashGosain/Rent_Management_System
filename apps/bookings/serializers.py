from rest_framework import serializers
from django.utils import timezone
from .models import Booking


class BookingSerializer(serializers.ModelSerializer):
    """Used for list and detail — read only nested info."""

    tenant_name = serializers.CharField(source="tenant.get_full_name", read_only=True)
    tenant_phone = serializers.CharField(source="tenant.phone", read_only=True)
    target_name = serializers.SerializerMethodField()
    target_type = serializers.SerializerMethodField()
    rent_price = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            "id",
            "status",
            "move_in_date",
            "move_out_date",
            "message",
            "owner_note",
            "cancelled_by",
            "created_at",
            "updated_at",
            "tenant_name",
            "tenant_phone",
            "target_name",
            "target_type",
            "rent_price",
            "owner_name",
            "property",
            "room",
        ]

    def get_target_name(self, obj):
        return obj.get_target_name()

    def get_target_type(self, obj):
        return "room" if obj.room else "property"

    def get_rent_price(self, obj):
        return obj.get_rent_price()

    def get_owner_name(self, obj):
        return obj.get_owner().get_full_name()


# ── Book a Property ───────────────────────────────────────────────────────────


class BookPropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ["move_in_date", "move_out_date", "message"]
        extra_kwargs = {
            "move_out_date": {"required": False},
            "message": {"required": False},
        }

    def validate(self, data):
        move_in = data.get("move_in_date")
        move_out = data.get("move_out_date")

        if move_in and move_in < timezone.now().date():
            raise serializers.ValidationError(
                {"move_in_date": "Move-in date cannot be in the past."}
            )
        if move_in and move_out and move_out <= move_in:
            raise serializers.ValidationError(
                {"move_out_date": "Move-out date must be after move-in date."}
            )
        return data

    def validate_property(self, prop):
        request = self.context["request"]
        # Only available whole properties
        if prop.status != "available":
            raise serializers.ValidationError("This property is not available.")
        if prop.rent_type != "whole":
            raise serializers.ValidationError(
                "This property rents individual rooms, not whole."
            )
        # Owner cannot book own property
        if prop.owner == request.user:
            raise serializers.ValidationError("You cannot book your own property.")
        # No duplicate pending booking
        if Booking.objects.filter(
            tenant=request.user, property=prop, status="pending"
        ).exists():
            raise serializers.ValidationError(
                "You already have a pending booking for this property."
            )
        return prop

    def create(self, validated_data):
        return Booking.objects.create(**validated_data)


# ── Book a Room ───────────────────────────────────────────────────────────────


class BookRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ["move_in_date", "move_out_date", "message"]
        extra_kwargs = {
            "move_out_date": {"required": False},
            "message": {"required": False},
        }

    def validate(self, data):
        move_in = data.get("move_in_date")
        move_out = data.get("move_out_date")

        if move_in and move_in < timezone.now().date():
            raise serializers.ValidationError(
                {"move_in_date": "Move-in date cannot be in the past."}
            )
        if move_in and move_out and move_out <= move_in:
            raise serializers.ValidationError(
                {"move_out_date": "Move-out date must be after move-in date."}
            )
        return data

    def validate_room(self, room):
        request = self.context["request"]
        if room.status != "available":
            raise serializers.ValidationError("This room is not available.")
        if room.property.owner == request.user:
            raise serializers.ValidationError("You cannot book your own room.")
        if Booking.objects.filter(
            tenant=request.user, room=room, status="pending"
        ).exists():
            raise serializers.ValidationError(
                "You already have a pending booking for this room."
            )
        return room

    def create(self, validated_data):
        return Booking.objects.create(**validated_data)


# ── Owner Response (accept / reject) ─────────────────────────────────────────


class OwnerResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ["owner_note"]
        extra_kwargs = {"owner_note": {"required": False}}
