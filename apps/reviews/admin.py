from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["reviewer", "review_type", "rating", "title", "created_at"]
    list_filter = ["review_type", "rating"]
    search_fields = ["reviewer__username", "title"]
