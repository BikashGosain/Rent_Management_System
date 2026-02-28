from django.urls import path
from . import views

app_name = 'agreements'

urlpatterns = [
    path('owner/',                      views.owner_agreements,  name='owner_agreements'),
    path('my/',                         views.tenant_agreements, name='tenant_agreements'),
    path('create/<int:booking_pk>/',    views.create_agreement,  name='create'),
    path('<int:pk>/',                   views.agreement_detail,  name='detail'),
    path('<int:pk>/sign/',              views.sign_agreement,    name='sign'),
    path('<int:pk>/terminate/',         views.terminate_agreement, name='terminate'),
    path('<int:pk>/delete/',            views.delete_agreement,  name='delete'),

    # Notice URLs
    path('<int:pk>/notice/submit/',     views.submit_notice,     name='submit_notice'),
    path('<int:pk>/notice/respond/',    views.respond_notice,    name='respond_notice'),
    path('<int:pk>/notice/cancel/',     views.cancel_notice,     name='cancel_notice'),
    path('<int:pk>/notice/complete/',   views.complete_vacate,   name='complete_vacate'),
]