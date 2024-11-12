from django.urls import path

from . import views as provider_views


urlpatterns = [
    path('', provider_views.provider_view, name='provider'),
    path('<int:id>/update_provider/', provider_views.update_provider, name='update_provider'),
    path('<int:id>/delete_provider/', provider_views.delete_provider, name='delete_provider'),

]