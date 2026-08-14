# apps/complaints/api_urls.py
from django.urls import path
from . import api_views

urlpatterns = [
    path("", api_views.SubmitComplaintAPI.as_view()),  # submit
    path("my/", api_views.MyComplaintsAPI.as_view()),  # tenant list
    path("owner/", api_views.OwnerComplaintsAPI.as_view()),  # owner list
    path("<int:pk>/", api_views.ComplaintDetailAPI.as_view()),  # detail
    path(
        "<int:pk>/status/", api_views.UpdateComplaintStatusAPI.as_view()
    ),  # update status
    path(
        "<int:pk>/respond/", api_views.AddComplaintResponseAPI.as_view()
    ),  # add response
    path("<int:pk>/delete/", api_views.DeleteComplaintAPI.as_view()),  # soft delete
]
