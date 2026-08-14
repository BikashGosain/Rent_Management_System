from django.urls import path
from . import api_views

urlpatterns = [
    # Properties
    path("properties/", api_views.PropertyListCreateAPI.as_view()),
    path("properties/<int:pk>/", api_views.PropertyDetailAPI.as_view()),
    # Rooms under a property
    path("properties/<int:property_id>/rooms/", api_views.RoomListCreateAPI.as_view()),
    # Individual room
    path("rooms/<int:pk>/", api_views.RoomDetailAPI.as_view()),
    # Room facilities
    path("rooms/<int:room_id>/facility/", api_views.RoomFacilityAPI.as_view()),
    # Global room search
    path("rooms/search/", api_views.RoomSearchAPI.as_view()),
]
