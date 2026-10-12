from django.urls import path
from .views import notification_list_view, mark_read_view, unread_badge_view

app_name = 'notifications'

urlpatterns = [
    path('', notification_list_view, name='list'),
    path('unread-badge/', unread_badge_view, name='unread_badge'),
    path('read/<int:notif_id>/', mark_read_view, name='mark_read'),
]
