from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ["tenant", "get_target_name", "status", "move_in_date", "created_at"]
    list_filter = ["status"]
    search_fields = ["tenant__username", "property__title", "room__room_number"]
