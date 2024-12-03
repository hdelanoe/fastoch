from django.urls import path

from . import views as delivery_views


urlpatterns = [
    path('', delivery_views.delivery_list_view, name='delivery_list'),
    path('<str:id>/delivery', delivery_views.delivery_view, name='delivery'),
    path('<str:delivery>/<str:id>/update_transaction', delivery_views.update_transaction, name='update_transaction'),
    path('<str:id>/validate_delivery', delivery_views.validate_delivery, name='validate_delivery'),
    path('<str:id>/export_delivery', delivery_views.export_delivery, name='export_delivery'),
    path('<str:id>/delete_delivery', delivery_views.delete_delivery, name='delete_delivery'),
    
    path('receipt', delivery_views.receipt_view, name='receipt'),
    path('export_receipt', delivery_views.export_receipt, name='export_receipt'),
    path('empty_receipt', delivery_views.empty_receipt, name='empty_receipt'),
]