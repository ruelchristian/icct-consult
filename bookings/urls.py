from django.urls import path
from .views import (
    book_faculty_view,
    htmx_get_slots,
    student_bookings_view,
    faculty_bookings_view,
    booking_detail_view,
    booking_action_view,
)

app_name = 'bookings'

urlpatterns = [
    path('book/<int:faculty_id>/', book_faculty_view, name='book_faculty'),
    path('htmx/slots/<int:faculty_id>/', htmx_get_slots, name='htmx_slots'),
    path('student/', student_bookings_view, name='student_bookings'),
    path('faculty/', faculty_bookings_view, name='faculty_bookings'),
    path('detail/<int:booking_id>/', booking_detail_view, name='booking_detail'),
    path('action/<int:booking_id>/', booking_action_view, name='booking_action'),
]
