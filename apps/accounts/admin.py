from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ["username", "email", "role", "is_active", "date_joined"]
    list_filter = ["role", "is_active"]
    search_fields = ["username", "email", "phone"]
    fieldsets = UserAdmin.fieldsets + (
        ("Role & Contact", {"fields": ("role", "phone", "photo")}),
    )
