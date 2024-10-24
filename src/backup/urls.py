from django.urls import path

from . import views as backup_views


urlpatterns = [
    path('', backup_views.backup_view, name='backup'),
    path('<int:id>/delete_backup/', backup_views.delete_backup, name='delete_backup'),


]