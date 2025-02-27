from django.urls import path

from . import views as inventory_views


urlpatterns = [
    path('<str:name>', inventory_views.inventory_view, name='inventory'),
    path('<str:id>/ask_question', inventory_views.ask_question, name='ask_question'),
    path('move_from_file', inventory_views.move_from_file, name='move_from_file'),
    path('import_inventory', inventory_views.import_inventory, name='import_inventory'),
    path('<str:id>/move_iproducts', inventory_views.move_iproducts, name='move_iproducts'),
    path('<str:id>/export_inventory', inventory_views.export_inventory, name='export_inventory'),
    path('<str:id>/backup_inventory', inventory_views.backup_inventory, name='backup_inventory'),
    path('<str:id>/delete_inventory', inventory_views.delete_inventory, name='delete_inventory'),

    path('update_product/<int:iproduct>/<int:product>', inventory_views.update_product, name='update_product'),
    #path('delete_product/<int:product>', inventory_views.delete_product, name='delete_product'),

    path('<int:id>/delete_iproduct', inventory_views.delete_iproduct, name='delete_iproduct'),

]
