from django.urls import path
from . import views

app_name = 'agreements'

urlpatterns = [
    # Owner
    path('owner/',                          views.owner_agreements,  name='owner_agreements'),
    path('create/<int:booking_pk>/',        views.create_agreement,  name='create'),

    # Tenant
    path('my/',                             views.tenant_agreements, name='tenant_agreements'),

    # Shared
    path('<int:pk>/',                       views.agreement_detail,  name='detail'),
    path('<int:pk>/sign/',                  views.sign_agreement,    name='sign'),
    path('<int:pk>/terminate/',             views.terminate_agreement, name='terminate'),
]