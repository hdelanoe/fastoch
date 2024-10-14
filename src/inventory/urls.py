from django.urls import path

from . import views as inventory_views


urlpatterns = [
    path('<str:id>/<int:response>', inventory_views.inventory_view, name='inventory'),
    path('<str:id>/ask_question', inventory_views.ask_question, name='ask_question'),
    path('<str:id>/add_from_pdf', inventory_views.add_from_pdf, name='add_from_pdf'),
    path('<str:id>/add_from_xml', inventory_views.add_from_xml, name='add_from_xml'),
    path('<str:id>/add_from_csv', inventory_views.add_from_csv, name='add_from_csv'),
    path('<str:id>/remove_from_pdf', inventory_views.remove_from_pdf, name='remove_from_pdf'),
    path('<str:id>/remove_from_xml', inventory_views.remove_from_xml, name='remove_from_xml'),
    path('<str:id>/remove_from_csv', inventory_views.remove_from_csv, name='remove_from_csv'),
    path('<str:id>/backup_inventory', inventory_views.backup_inventory, name='backup_inventory'),
    path('<str:id>/export_inventory', inventory_views.export_inventory, name='export_inventory'),

    path('<int:inventory>/update_product/<int:product>', inventory_views.update_product, name='update_product'),
]
