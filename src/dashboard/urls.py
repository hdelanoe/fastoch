from django.urls import include, path

from . import views as dashboard_views


urlpatterns = [
    path('', dashboard_views.dashboard_view, name='dashboard'),
    path('inventory/', include('inventory.urls')),
    path('backup/', include('backup.urls')),
    path('provider/', include('provider.urls')),
    path('delivery/', include('delivery.urls')),

    path('create_inventory/', dashboard_views.create_inventory),


]
