from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('',                        views.notification_list,  name='list'),
    path('<int:pk>/read/',          views.mark_read,          name='mark_read'),
    path('<int:pk>/mark-read/',     views.mark_single_read,   name='mark_single_read'),
    path('<int:pk>/delete/',        views.delete_single,      name='delete_single'),
    path('mark-all-read/',          views.mark_all_read,      name='mark_all_read'),
    path('delete-all/',             views.delete_all,         name='delete_all'),
    path('unread-count/',           views.unread_count,       name='unread_count'),
]