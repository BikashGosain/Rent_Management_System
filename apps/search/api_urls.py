# apps/search/api_urls.py
from django.urls import path
from . import api_views

urlpatterns = [
    path('', api_views.SearchAPI.as_view()),  # GET /api/search/
]