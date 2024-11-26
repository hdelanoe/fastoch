from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from .views import dashboard_view, create_inventory

urlpatterns = [
    path('', dashboard_view, name='dashboard'),
    path('create_inventory/', create_inventory),
]    
