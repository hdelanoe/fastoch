from django.urls import path

from . import views as inventory_views


urlpatterns = [
    path('<str:id>/<int:response>', inventory_views.inventory_view, name='inventory'),
    path('<str:id>/ask_question', inventory_views.ask_question, name='ask_question'),
    path('<str:id>/upload_pdf', inventory_views.upload_pdf, name='upload_pdf'),
    path('<str:id>/upload_xml', inventory_views.upload_xml, name='upload_xml'),
    path('<str:id>/upload_csv', inventory_views.upload_csv, name='upload_csv'),
    path('<str:id>/backup_inventory', inventory_views.backup_inventory, name='backup_inventory'),
    path('<str:id>/export_inventory', inventory_views.export_inventory, name='export_inventory'),

    path('<int:inventory>/update_product/<int:product>', inventory_views.update_product, name='update_product'),


]
