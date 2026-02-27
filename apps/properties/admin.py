from django.contrib import admin
from .models import Property, PropertyPhoto, Room, RoomPhoto


class PropertyPhotoInline(admin.TabularInline):
    model = PropertyPhoto
    extra = 1


class RoomInline(admin.TabularInline):
    model  = Room
    extra  = 0
    fields = ['room_number', 'room_type', 'rent_price', 'status']


class RoomPhotoInline(admin.TabularInline):
    model = RoomPhoto
    extra = 1


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display  = ['title', 'type', 'rent_type', 'city', 'status', 'owner']
    list_filter   = ['type', 'rent_type', 'status', 'city']
    search_fields = ['title', 'address', 'city', 'owner__username']

    def get_inlines(self, request, obj=None):
        """Show RoomInline only for properties with rent_type='rooms'."""
        if obj and obj.rent_type == 'rooms':
            return [PropertyPhotoInline, RoomInline]
        return [PropertyPhotoInline]


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display  = ['room_number', 'property', 'room_type', 'rent_price', 'status']
    list_filter   = ['status', 'room_type', 'furnishing']
    search_fields = ['room_number', 'property__title', 'property__owner__username']
    inlines       = [RoomPhotoInline]