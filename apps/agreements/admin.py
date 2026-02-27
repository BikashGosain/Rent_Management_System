from django.contrib import admin
from .models import Agreement


@admin.register(Agreement)
class AgreementAdmin(admin.ModelAdmin):
    list_display  = ['owner', 'tenant', 'get_target_name', 'status', 'start_date', 'end_date']
    list_filter   = ['status']
    search_fields = ['owner__username', 'tenant__username']