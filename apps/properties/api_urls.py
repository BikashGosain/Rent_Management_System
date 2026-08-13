from django.urls import path
from . import api_views

urlpatterns = [
    path('properties/',                        api_views.PropertyListCreateAPI.as_view()),
    path('properties/<int:pk>/',               api_views.PropertyDetailAPI.as_view()),
    path('properties/<int:property_id>/rooms/',api_views.RoomListCreateAPI.as_view()),
    path('rooms/<int:pk>/',                    api_views.RoomDetailAPI.as_view()),
]