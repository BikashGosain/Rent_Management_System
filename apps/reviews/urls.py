from django.urls import path
from . import views

app_name = "reviews"

urlpatterns = [
    path("my/", views.my_reviews, name="my_reviews"),
    path("received/", views.reviews_received, name="received"),
    path(
        "write/<int:agreement_pk>/<str:review_type>/", views.write_review, name="write"
    ),
    path("property/<int:pk>/", views.property_reviews, name="property_reviews"),
    path("room/<int:pk>/", views.room_reviews, name="room_reviews"),
    path("<int:pk>/delete/", views.delete_review, name="delete"),
]
