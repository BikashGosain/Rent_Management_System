from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Owner
    path('owner/',                                  views.owner_payments,          name='owner_payments'),
    path('create/<int:agreement_pk>/',              views.create_payment,          name='create'),
    path('auto-generate/<int:agreement_pk>/',       views.auto_generate_payments,  name='auto_generate'),
    path('<int:pk>/mark-paid/',                     views.mark_paid,               name='mark_paid'),
    path('<int:pk>/cancel/',                        views.cancel_payment,          name='cancel'),

    # Tenant
    path('my/',                                     views.tenant_payments,         name='tenant_payments'),

    # Shared
    path('<int:pk>/',                               views.payment_detail,          name='detail'),

    path('<int:pk>/delete/', views.delete_payment, name='delete'),
]