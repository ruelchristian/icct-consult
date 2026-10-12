from django.urls import path
from .views import home_view, service_worker_view, manifest_view, offline_view

app_name = 'core'

urlpatterns = [
    path('', home_view, name='home'),
    path('sw.js', service_worker_view, name='service_worker'),
    path('manifest.json', manifest_view, name='manifest'),
    path('offline/', offline_view, name='offline'),
]
