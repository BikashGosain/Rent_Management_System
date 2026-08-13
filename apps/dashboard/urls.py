from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("admin/", views.admin_dashboard, name="admin"),
    path("owner/", views.owner_dashboard, name="owner"),
    path("tenant/", views.tenant_dashboard, name="tenant"),
    path("", views.dashboard_redirect, name="redirect"),
]
