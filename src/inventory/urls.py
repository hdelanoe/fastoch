from django.urls import path

from . import views as inventory_views


urlpatterns = [
    path('<str:id>', inventory_views.inventory_view, name='inventory'),
    path('<str:id>/upload_file', inventory_views.upload_file, name='upload_file'),
    path('<str:id>/export_file', inventory_views.export_file, name='export_file'),
]
