from django.urls import path
from .views import faculty_calendar_events_json, manage_slots_view, delete_slot_view

app_name = 'availability'

urlpatterns = [
    path('faculty/<int:faculty_id>/events.json', faculty_calendar_events_json, name='calendar_events_json'),
    path('manage/', manage_slots_view, name='manage_slots'),
    path('delete/<int:slot_id>/', delete_slot_view, name='delete_slot'),
]
