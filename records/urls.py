from django.urls import path
from .views import add_edit_session_record_view, view_session_record_view

app_name = 'records'

urlpatterns = [
    path('edit/<int:booking_id>/', add_edit_session_record_view, name='record_edit'),
    path('view/<int:booking_id>/', view_session_record_view, name='record_detail'),
]
