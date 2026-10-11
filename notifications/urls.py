from django.urls import path
from .views import notification_list_view, mark_read_view

app_name = 'notifications'

urlpatterns = [
    path('', notification_list_view, name='list'),
    path('read/<int:notif_id>/', mark_read_view, name='mark_read'),
]
