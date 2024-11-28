from django.urls import path

from . import views as settings_views


urlpatterns = [
    path('', settings_views.settings_view, name='settings')
]