from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("recycle-bin/", views.recycle_bin, name="recycle_bin"),
    path(
        "recycle-bin/restore/<str:model>/<int:pk>/", views.restore_item, name="restore"
    ),
    path(
        "recycle-bin/delete/<str:model>/<int:pk>/",
        views.permanent_delete,
        name="permanent_delete",
    ),
    path("recycle-bin/restore-all/", views.restore_all, name="restore_all"),
    path(
        "recycle-bin/delete-all/",
        views.permanent_delete_all,
        name="permanent_delete_all",
    ),
]
