from django.urls import path

from . import views as settings_views


urlpatterns = [
    path('', settings_views.settings_view, name='settings'),
    path('documentation/', settings_views.documentation_view, name='documentation'),
    path('download_logfile/', settings_views.download_logfile, name='download_logfile'),
    path('preferences/', settings_views.update_preferences, name='preferences'),
    path('delete_media_files/', settings_views.delete_media_files, name='delete_media_files'),
]