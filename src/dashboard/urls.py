from django.urls import path

from . import views as dashboard_views
from inventory import views as inventory_views


urlpatterns = [
    path('', dashboard_views.dashboard_view, name='dashboard'),
    path('inventory/<str:name>', inventory_views.inventory_view, name='inventory'),

    path('create_inventory/', dashboard_views.create_inventory),

   
]