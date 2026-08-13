from django.contrib import admin
from .models import Complaint, ComplaintResponse


class ComplaintResponseInline(admin.TabularInline):
    model = ComplaintResponse
    extra = 0


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "category",
        "priority",
        "status",
        "tenant",
        "owner",
        "created_at",
    ]
    list_filter = ["status", "category", "priority"]
    search_fields = ["title", "tenant__username", "owner__username"]
    inlines = [ComplaintResponseInline]


@admin.register(ComplaintResponse)
class ComplaintResponseAdmin(admin.ModelAdmin):
    list_display = ["complaint", "responder", "created_at"]
