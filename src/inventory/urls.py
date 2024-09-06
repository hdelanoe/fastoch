from django.urls import path

from . import views as inventory_views


urlpatterns = [
    path('<str:name>', inventory_views.inventory_view, name='inventory'),
    path('<str:name>/upload_file', inventory_views.upload_file, name='upload_file'),
]
