from django.urls import path
from . import views

app_name = 'properties'

urlpatterns = [
    # Property URLs
    path('',                          views.property_list,   name='list'),
    path('add/',                      views.property_add,    name='add'),
    path('<int:pk>/',                 views.property_detail, name='detail'),
    path('<int:pk>/edit/',            views.property_edit,   name='edit'),
    path('<int:pk>/delete/',          views.property_delete, name='delete'),

    # Room URLs
    path('<int:pk>/rooms/add/',                       views.room_add,    name='room_add'),
    path('<int:pk>/rooms/<int:room_pk>/',             views.room_detail, name='room_detail'),
    path('<int:pk>/rooms/<int:room_pk>/edit/',        views.room_edit,   name='room_edit'),
    path('<int:pk>/rooms/<int:room_pk>/delete/',      views.room_delete, name='room_delete'),
]