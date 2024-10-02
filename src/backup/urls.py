from django.urls import path

from . import views as backup_views


urlpatterns = [
    path('', backup_views.backup_view, name='backup'),

]