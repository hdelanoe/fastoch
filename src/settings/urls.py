from django.urls import path

from . import views as settings_views


urlpatterns = [
    path('', settings_views.settings_view, name='settings'),
    path('documentation/', settings_views.documentation_view, name='documentation'),
    path('download_logfile/', settings_views.download_logfile, name='download_logfile')
]