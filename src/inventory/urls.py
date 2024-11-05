from django.urls import path

from . import views as inventory_views


urlpatterns = [
    path('<str:id>/<int:response>', inventory_views.inventory_view, name='inventory'),
    path('<str:id>/ask_question', inventory_views.ask_question, name='ask_question'),
    path('<str:id>/move_from_file', inventory_views.move_from_file, name='move_from_file'),
    path('<str:id>/import_inventory', inventory_views.import_inventory, name='import_inventory'),
    path('<str:id>/export_inventory', inventory_views.export_inventory, name='export_inventory'),
    path('<str:id>/backup_inventory', inventory_views.backup_inventory, name='backup_inventory'),


    path('<int:inventory>/update_product/<int:product>', inventory_views.update_product, name='update_product'),
    path('<int:inventory>/delete_product/<int:product>', inventory_views.delete_product, name='delete_product'),
]
