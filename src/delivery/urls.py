from django.urls import path

from . import views as delivery_views


urlpatterns = [
    path('', delivery_views.delivery_view, name='delivery'),
    path('<str:id>/last_delivery', delivery_views.last_delivery_view, name='last_delivery'),
    path('<str:id>/export_delivery', delivery_views.export_delivery, name='export_delivery'),

]