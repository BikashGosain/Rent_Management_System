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
    search_fields = ['title', 'address', 'city']
    inlines       = [PropertyPhotoInline, RoomInline]


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display  = ['room_number', 'property', 'room_type', 'rent_price', 'status']
    list_filter   = ['status', 'room_type', 'furnishing']
    search_fields = ['room_number', 'property__title']
    inlines       = [RoomPhotoInline]
