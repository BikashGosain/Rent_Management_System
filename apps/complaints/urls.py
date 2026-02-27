from django.urls import path
from . import views

app_name = 'complaints'

urlpatterns = [
    # Tenant
    path('submit/',       views.submit_complaint, name='submit'),
    path('my/',           views.my_complaints,    name='my_complaints'),

    # Owner
    path('owner/',        views.owner_complaints, name='owner_complaints'),
    path('owner/raise/<int:agreement_pk>/',      views.owner_submit_complaint, name='owner_submit'),

    # Admin
    path('admin/',        views.admin_complaints, name='admin_complaints'),

    # Shared
    path('<int:pk>/',     views.complaint_detail, name='detail'),
]