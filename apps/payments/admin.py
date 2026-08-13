from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["tenant", "owner", "payment_type", "amount", "due_date", "status"]
    list_filter = ["status", "payment_type", "payment_method"]
    search_fields = ["tenant__username", "owner__username"]
