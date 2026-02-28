from django.urls import path
from . import views

app_name = 'bookmarks'

urlpatterns = [
    path('',                                          views.bookmark_list,             name='list'),
    path('toggle/property/<int:pk>/',                 views.toggle_property_bookmark,  name='toggle_property'),
    path('toggle/room/<int:property_pk>/<int:room_pk>/', views.toggle_room_bookmark,   name='toggle_room'),
    path('<int:pk>/remove/',                          views.remove_bookmark,           name='remove'),
    path('<int:pk>/compare/',                         views.toggle_compare,            name='toggle_compare'),
    path('compare/',                                  views.compare_view,              name='compare'),
    path('compare/clear/',                            views.clear_compare,             name='clear_compare'),
]