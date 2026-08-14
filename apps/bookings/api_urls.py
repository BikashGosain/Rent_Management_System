from django.urls import path
from . import api_views

urlpatterns = [
    # Tenant
    path(
        "property/<int:pk>/", api_views.BookPropertyAPI.as_view()
    ),  # book whole property
    path("room/<int:room_pk>/", api_views.BookRoomAPI.as_view()),  # book a room
    path("my/", api_views.MyBookingsAPI.as_view()),  # my bookings list
    path("<int:pk>/cancel/", api_views.CancelBookingAPI.as_view()),  # tenant cancel
    # Owner
    path("owner/", api_views.OwnerBookingsAPI.as_view()),  # owner bookings list
    path("<int:pk>/accept/", api_views.AcceptBookingAPI.as_view()),  # accept
    path("<int:pk>/reject/", api_views.RejectBookingAPI.as_view()),  # reject
    path(
        "<int:pk>/owner-cancel/", api_views.OwnerCancelBookingAPI.as_view()
    ),  # owner cancel
    # Both
    path("<int:pk>/", api_views.BookingDetailAPI.as_view()),  # detail
    path("<int:pk>/delete/", api_views.DeleteBookingAPI.as_view()),  # soft delete
]
