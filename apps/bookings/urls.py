from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    # Tenant
    path('my/',                                              views.my_bookings,       name='my_bookings'),
    path('property/<int:pk>/book/',                          views.book_property,     name='book_property'),
    path('property/<int:property_pk>/room/<int:room_pk>/book/', views.book_room,      name='book_room'),
    path('<int:pk>/cancel/',                                 views.cancel_booking,    name='cancel'),

    # Owner
    path('owner/',                                           views.owner_bookings,    name='owner_bookings'),
    path('<int:pk>/',                                        views.booking_detail,    name='detail'),
    path('<int:pk>/accept/',                                 views.accept_booking,    name='accept'),
    path('<int:pk>/reject/',                                 views.reject_booking,    name='reject'),
    path('<int:pk>/owner-cancel/',                           views.owner_cancel_booking, name='owner_cancel'),

    path('<int:pk>/delete/', views.delete_booking, name='delete'),
]